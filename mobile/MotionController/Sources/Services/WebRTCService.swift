import Foundation
import WebRTC
import Combine

protocol WebRTCServiceDelegate: AnyObject {
    func webRTCService(_ service: WebRTCService, didGenerateCandidate candidate: RTCIceCandidate)
    func webRTCService(_ service: WebRTCService, didChangeConnectionState state: RTCIceConnectionState)
    func webRTCServiceDidOpenDataChannel(_ service: WebRTCService)
    func webRTCServiceDidCloseDataChannel(_ service: WebRTCService)
}

final class WebRTCService: NSObject, ObservableObject {
    weak var delegate: WebRTCServiceDelegate?

    @Published var isDataChannelOpen = false

    private static let factory: RTCPeerConnectionFactory = {
        RTCInitializeSSL()
        return RTCPeerConnectionFactory()
    }()

    private var peerConnection: RTCPeerConnection?
    private var dataChannel: RTCDataChannel?

    // MARK: - Setup

    func setup() {
        let config = RTCConfiguration()
        config.iceServers = Constants.STUN.servers.map { RTCIceServer(urlStrings: [$0]) }
        config.sdpSemantics = .unifiedPlan
        config.continualGatheringPolicy = .gatherContinually

        let constraints = RTCMediaConstraints(
            mandatoryConstraints: nil,
            optionalConstraints: nil
        )

        peerConnection = Self.factory.peerConnection(
            with: config,
            constraints: constraints,
            delegate: self
        )

        createDataChannel()
    }

    func teardown() {
        dataChannel?.close()
        dataChannel = nil
        peerConnection?.close()
        peerConnection = nil
        DispatchQueue.main.async {
            self.isDataChannelOpen = false
        }
    }

    // MARK: - Offer/Answer

    func createOffer() async throws -> RTCSessionDescription {
        guard let peerConnection else {
            throw WebRTCError.noPeerConnection
        }

        let constraints = RTCMediaConstraints(
            mandatoryConstraints: [
                "OfferToReceiveAudio": "false",
                "OfferToReceiveVideo": "false"
            ],
            optionalConstraints: nil
        )

        return try await withCheckedThrowingContinuation { continuation in
            peerConnection.offer(for: constraints) { sdp, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                guard let sdp else {
                    continuation.resume(throwing: WebRTCError.failedToCreateOffer)
                    return
                }
                peerConnection.setLocalDescription(sdp) { error in
                    if let error {
                        continuation.resume(throwing: error)
                    } else {
                        continuation.resume(returning: sdp)
                    }
                }
            }
        }
    }

    func setRemoteDescription(_ sdp: RTCSessionDescription) async throws {
        guard let peerConnection else {
            throw WebRTCError.noPeerConnection
        }

        return try await withCheckedThrowingContinuation { continuation in
            peerConnection.setRemoteDescription(sdp) { error in
                if let error {
                    continuation.resume(throwing: error)
                } else {
                    continuation.resume()
                }
            }
        }
    }

    func addIceCandidate(_ candidate: RTCIceCandidate) async throws {
        guard let peerConnection else {
            throw WebRTCError.noPeerConnection
        }

        return try await withCheckedThrowingContinuation { continuation in
            peerConnection.add(candidate) { error in
                if let error {
                    continuation.resume(throwing: error)
                } else {
                    continuation.resume()
                }
            }
        }
    }

    // MARK: - Data Channel

    func sendData(_ data: Data) {
        guard let dataChannel, dataChannel.readyState == .open else { return }
        let buffer = RTCDataBuffer(data: data, isBinary: false)
        dataChannel.sendData(buffer)
    }

    private func createDataChannel() {
        let config = RTCDataChannelConfiguration()
        config.isOrdered = Constants.DataChannel.isOrdered
        config.maxRetransmits = Constants.DataChannel.maxRetransmits
        config.isNegotiated = false

        dataChannel = peerConnection?.dataChannel(
            forLabel: Constants.DataChannel.label,
            configuration: config
        )
        dataChannel?.delegate = self
    }

    deinit {
        teardown()
    }
}

// MARK: - RTCPeerConnectionDelegate

extension WebRTCService: RTCPeerConnectionDelegate {
    func peerConnection(_ peerConnection: RTCPeerConnection, didChange stateChanged: RTCSignalingState) {
        print("[WebRTC] Signaling state: \(stateChanged.rawValue)")
    }

    func peerConnection(_ peerConnection: RTCPeerConnection, didAdd stream: RTCMediaStream) {}

    func peerConnection(_ peerConnection: RTCPeerConnection, didRemove stream: RTCMediaStream) {}

    func peerConnectionShouldNegotiate(_ peerConnection: RTCPeerConnection) {
        print("[WebRTC] Should negotiate")
    }

    func peerConnection(_ peerConnection: RTCPeerConnection, didChange newState: RTCIceConnectionState) {
        print("[WebRTC] ICE connection state: \(newState.rawValue)")
        delegate?.webRTCService(self, didChangeConnectionState: newState)
    }

    func peerConnection(_ peerConnection: RTCPeerConnection, didChange newState: RTCIceGatheringState) {
        print("[WebRTC] ICE gathering state: \(newState.rawValue)")
    }

    func peerConnection(_ peerConnection: RTCPeerConnection, didGenerate candidate: RTCIceCandidate) {
        delegate?.webRTCService(self, didGenerateCandidate: candidate)
    }

    func peerConnection(_ peerConnection: RTCPeerConnection, didRemove candidates: [RTCIceCandidate]) {}

    func peerConnection(_ peerConnection: RTCPeerConnection, didOpen dataChannel: RTCDataChannel) {
        self.dataChannel = dataChannel
        dataChannel.delegate = self
    }
}

// MARK: - RTCDataChannelDelegate

extension WebRTCService: RTCDataChannelDelegate {
    func dataChannelDidChangeState(_ dataChannel: RTCDataChannel) {
        print("[WebRTC] DataChannel state: \(dataChannel.readyState.rawValue)")
        let isOpen = dataChannel.readyState == .open
        DispatchQueue.main.async {
            self.isDataChannelOpen = isOpen
        }
        if isOpen {
            delegate?.webRTCServiceDidOpenDataChannel(self)
        } else if dataChannel.readyState == .closed {
            delegate?.webRTCServiceDidCloseDataChannel(self)
        }
    }

    func dataChannel(_ dataChannel: RTCDataChannel, didReceiveMessageWith buffer: RTCDataBuffer) {}
}

// MARK: - Errors

enum WebRTCError: LocalizedError {
    case noPeerConnection
    case failedToCreateOffer

    var errorDescription: String? {
        switch self {
        case .noPeerConnection: return "No peer connection available"
        case .failedToCreateOffer: return "Failed to create SDP offer"
        }
    }
}
