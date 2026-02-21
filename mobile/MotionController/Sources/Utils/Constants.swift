import Foundation

enum Constants {
    static let sensorUpdateInterval: TimeInterval = 1.0 / 60.0 // 60Hz

    enum STUN {
        static let servers = [
            "stun:stun.l.google.com:19302",
            "stun:stun1.l.google.com:19302"
        ]
    }

    enum DataChannel {
        static let label = "sensor_data"
        static let isOrdered = false
        static let maxRetransmits: Int32 = 0
    }

    enum Signaling {
        static let serverURL = "wss://signaling-server-1081248663051.asia-northeast1.run.app/ws"
        static let reconnectDelay: TimeInterval = 3.0
        static let maxReconnectAttempts = 5
    }
}
