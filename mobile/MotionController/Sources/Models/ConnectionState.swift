import Foundation

enum ConnectionState: String, Sendable {
    case disconnected = "Disconnected"
    case connectingSignaling = "Connecting to server..."
    case signalingConnected = "Server connected"
    case creatingOffer = "Creating offer..."
    case waitingForAnswer = "Waiting for answer..."
    case settingRemoteDescription = "Setting remote description..."
    case exchangingICE = "Exchanging ICE candidates..."
    case connected = "Connected"
    case failed = "Connection failed"

    var isConnected: Bool {
        self == .connected
    }

    var isConnecting: Bool {
        switch self {
        case .connectingSignaling, .signalingConnected, .creatingOffer,
             .waitingForAnswer, .settingRemoteDescription, .exchangingICE:
            return true
        default:
            return false
        }
    }

    var statusColor: String {
        switch self {
        case .connected: return "green"
        case .disconnected, .failed: return "red"
        default: return "orange"
        }
    }
}
