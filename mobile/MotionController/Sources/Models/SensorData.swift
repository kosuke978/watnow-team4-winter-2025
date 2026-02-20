import Foundation

struct Vector3: Codable, Sendable {
    var x: Double
    var y: Double
    var z: Double

    static let zero = Vector3(x: 0, y: 0, z: 0)

    static func - (lhs: Vector3, rhs: Vector3) -> Vector3 {
        Vector3(x: lhs.x - rhs.x, y: lhs.y - rhs.y, z: lhs.z - rhs.z)
    }
}

struct Rotation: Codable, Sendable {
    var pitch: Double
    var roll: Double
    var yaw: Double

    static let zero = Rotation(pitch: 0, roll: 0, yaw: 0)

    static func - (lhs: Rotation, rhs: Rotation) -> Rotation {
        Rotation(pitch: lhs.pitch - rhs.pitch, roll: lhs.roll - rhs.roll, yaw: lhs.yaw - rhs.yaw)
    }
}

struct SensorData: Codable, Sendable {
    let type: String
    let timestamp: TimeInterval
    let playerId: Int
    let acceleration: Vector3
    let rotation: Rotation
    let calibrated: Bool

    init(acceleration: Vector3, rotation: Rotation, calibrated: Bool, playerId: Int = 1) {
        self.type = "sensor_data"
        self.timestamp = Date().timeIntervalSince1970
        self.playerId = playerId
        self.acceleration = acceleration
        self.rotation = rotation
        self.calibrated = calibrated
    }

    func jsonData() -> Data? {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        return try? encoder.encode(self)
    }
}
