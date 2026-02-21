import Foundation
import Combine

@MainActor
final class ConnectionViewModel: ObservableObject {
    @Published var connectionState: ConnectionState = .disconnected
    @Published var errorMessage: String?
    @Published var assignedPlayerId: Int?
    @Published var playerName: String = ""

    let signalingService = SignalingService()

    init() {
        signalingService.delegate = self
    }

    // MARK: - Public

    func connect() {
        guard let url = URL(string: Constants.Signaling.serverURL) else {
            errorMessage = "Invalid server URL"
            return
        }

        errorMessage = nil
        connectionState = .connecting
        signalingService.connect(to: url)
    }

    func disconnect() {
        signalingService.disconnect()
        connectionState = .disconnected
        assignedPlayerId = nil
    }
}

// MARK: - SignalingServiceDelegate

extension ConnectionViewModel: SignalingServiceDelegate {
    nonisolated func signalingService(_ service: SignalingService, didReceiveMessage message: SignalingMessage) {
        // サーバーからのメッセージは無視（リレー専用）
    }

    nonisolated func signalingService(_ service: SignalingService, didAssignPlayerId playerId: Int) {
        DispatchQueue.main.async {
            self.assignedPlayerId = playerId
        }
    }

    nonisolated func signalingServiceDidConnect(_ service: SignalingService) {
        DispatchQueue.main.async {
            self.connectionState = .connected
            self.errorMessage = nil

            let name = self.playerName.trimmingCharacters(in: .whitespacesAndNewlines)
            if !name.isEmpty {
                service.sendPlayerName(name)
            }
        }
    }

    nonisolated func signalingServiceDidDisconnect(_ service: SignalingService) {
        DispatchQueue.main.async {
            if self.connectionState != .disconnected {
                self.connectionState = .failed
                self.errorMessage = "Server connection lost"
            }
            self.assignedPlayerId = nil
        }
    }
}
