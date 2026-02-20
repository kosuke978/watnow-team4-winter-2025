import Foundation

enum ConnectionState: String, Sendable {
    case disconnected = "Disconnected"
    case connecting = "Connecting to server..."
    case connected = "Connected"
    case failed = "Connection failed"

    var isConnected: Bool {
        self == .connected
    }

    var isConnecting: Bool {
        self == .connecting
    }

    var statusColor: String {
        switch self {
        case .connected: return "green"
        case .disconnected, .failed: return "red"
        default: return "orange"
        }
    }
}
