import Foundation
import WebRTC
import Combine

@MainActor
final class ConnectionViewModel: ObservableObject {
    @Published var connectionState: ConnectionState = .disconnected
    @Published var serverURLString: String = ""
    @Published var recentServers: [String] = []
    @Published var errorMessage: String?

    let signalingService = SignalingService()
    let webRTCService = WebRTCService()

    private let clientId = UUID().uuidString
    private var cancellables = Set<AnyCancellable>()

    init() {
        loadSavedData()
        signalingService.delegate = self
        webRTCService.delegate = self
    }

    // MARK: - Public

    func connect() {
        guard let url = URL(string: serverURLString),
              serverURLString.hasPrefix("ws://") || serverURLString.hasPrefix("wss://") else {
            errorMessage = "Invalid URL. Use ws:// or wss:// prefix."
            return
        }

        errorMessage = nil
        connectionState = .connectingSignaling

        webRTCService.setup()
        signalingService.connect(to: url)

        saveServer(serverURLString)
    }

    func disconnect() {
        signalingService.disconnect()
        webRTCService.teardown()
        connectionState = .disconnected
    }

    func selectRecentServer(_ server: String) {
        serverURLString = server
    }

    // MARK: - Private

    private func startOffer() {
        connectionState = .creatingOffer

        Task {
            do {
                let offer = try await webRTCService.createOffer()
                let message = SignalingMessage.offer(sdp: offer.sdp, clientId: clientId)
                signalingService.send(message)
                connectionState = .waitingForAnswer
            } catch {
                connectionState = .failed
                errorMessage = "Failed to create offer: \(error.localizedDescription)"
            }
        }
    }

    private func handleAnswer(sdp: String) {
        connectionState = .settingRemoteDescription

        Task {
            do {
                let description = RTCSessionDescription(type: .answer, sdp: sdp)
                try await webRTCService.setRemoteDescription(description)
                connectionState = .exchangingICE
            } catch {
                connectionState = .failed
                errorMessage = "Failed to set remote description: \(error.localizedDescription)"
            }
        }
    }

    private func handleIceCandidate(candidate: String, sdpMid: String?, sdpMLineIndex: Int32) {
        Task {
            do {
                let iceCandidate = RTCIceCandidate(
                    sdp: candidate,
                    sdpMLineIndex: sdpMLineIndex,
                    sdpMid: sdpMid
                )
                try await webRTCService.addIceCandidate(iceCandidate)
            } catch {
                print("[Connection] Failed to add ICE candidate: \(error.localizedDescription)")
            }
        }
    }

    // MARK: - Persistence

    private func loadSavedData() {
        serverURLString = UserDefaults.standard.string(forKey: Constants.UserDefaultsKeys.serverURL)
            ?? "ws://192.168.1.100:8080/ws"
        recentServers = UserDefaults.standard.stringArray(forKey: Constants.UserDefaultsKeys.recentServers) ?? []
    }

    private func saveServer(_ server: String) {
        UserDefaults.standard.set(server, forKey: Constants.UserDefaultsKeys.serverURL)

        var servers = recentServers
        servers.removeAll { $0 == server }
        servers.insert(server, at: 0)
        if servers.count > 5 {
            servers = Array(servers.prefix(5))
        }
        recentServers = servers
        UserDefaults.standard.set(servers, forKey: Constants.UserDefaultsKeys.recentServers)
    }
}

// MARK: - SignalingServiceDelegate

extension ConnectionViewModel: SignalingServiceDelegate {
    nonisolated func signalingService(_ service: SignalingService, didReceiveMessage message: SignalingMessage) {
        DispatchQueue.main.async {
            switch message {
            case .answer(let sdp, _):
                self.handleAnswer(sdp: sdp)
            case .ice(let candidate, let sdpMid, let sdpMLineIndex, _):
                self.handleIceCandidate(candidate: candidate, sdpMid: sdpMid, sdpMLineIndex: sdpMLineIndex)
            case .offer:
                break // iOS app only sends offers, doesn't receive them
            }
        }
    }

    nonisolated func signalingServiceDidConnect(_ service: SignalingService) {
        DispatchQueue.main.async {
            self.connectionState = .signalingConnected
            self.startOffer()
        }
    }

    nonisolated func signalingServiceDidDisconnect(_ service: SignalingService) {
        DispatchQueue.main.async {
            if self.connectionState != .disconnected {
                self.connectionState = .failed
                self.errorMessage = "Server connection lost"
            }
        }
    }
}

// MARK: - WebRTCServiceDelegate

extension ConnectionViewModel: WebRTCServiceDelegate {
    nonisolated func webRTCService(_ service: WebRTCService, didGenerateCandidate candidate: RTCIceCandidate) {
        let message = SignalingMessage.ice(
            candidate: candidate.sdp,
            sdpMid: candidate.sdpMid,
            sdpMLineIndex: candidate.sdpMLineIndex,
            clientId: clientId
        )
        signalingService.send(message)
    }

    nonisolated func webRTCService(_ service: WebRTCService, didChangeConnectionState state: RTCIceConnectionState) {
        DispatchQueue.main.async {
            switch state {
            case .connected, .completed:
                break // Wait for DataChannel open
            case .failed:
                self.connectionState = .failed
                self.errorMessage = "WebRTC connection failed"
            case .disconnected:
                if self.connectionState == .connected {
                    self.connectionState = .failed
                    self.errorMessage = "WebRTC disconnected"
                }
            default:
                break
            }
        }
    }

    nonisolated func webRTCServiceDidOpenDataChannel(_ service: WebRTCService) {
        DispatchQueue.main.async {
            self.connectionState = .connected
            self.errorMessage = nil
        }
    }

    nonisolated func webRTCServiceDidCloseDataChannel(_ service: WebRTCService) {
        DispatchQueue.main.async {
            if self.connectionState == .connected {
                self.connectionState = .failed
                self.errorMessage = "Data channel closed"
            }
        }
    }
}
