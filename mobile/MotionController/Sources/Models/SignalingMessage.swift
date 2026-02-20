import Foundation

enum SignalingMessage: Codable, Sendable {
    case offer(sdp: String, clientId: String)
    case answer(sdp: String, clientId: String)
    case ice(candidate: String, sdpMid: String?, sdpMLineIndex: Int32, clientId: String)

    enum CodingKeys: String, CodingKey {
        case type
        case sdp
        case clientId = "client_id"
        case candidate
        case sdpMid = "sdpMid"
        case sdpMLineIndex = "sdpMLineIndex"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let type = try container.decode(String.self, forKey: .type)

        switch type {
        case "offer":
            let sdp = try container.decode(String.self, forKey: .sdp)
            let clientId = try container.decode(String.self, forKey: .clientId)
            self = .offer(sdp: sdp, clientId: clientId)
        case "answer":
            let sdp = try container.decode(String.self, forKey: .sdp)
            let clientId = try container.decode(String.self, forKey: .clientId)
            self = .answer(sdp: sdp, clientId: clientId)
        case "ice":
            let candidate = try container.decode(String.self, forKey: .candidate)
            let sdpMid = try container.decodeIfPresent(String.self, forKey: .sdpMid)
            let sdpMLineIndex = try container.decode(Int32.self, forKey: .sdpMLineIndex)
            let clientId = try container.decode(String.self, forKey: .clientId)
            self = .ice(candidate: candidate, sdpMid: sdpMid, sdpMLineIndex: sdpMLineIndex, clientId: clientId)
        default:
            throw DecodingError.dataCorruptedError(
                forKey: .type,
                in: container,
                debugDescription: "Unknown message type: \(type)"
            )
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)

        switch self {
        case .offer(let sdp, let clientId):
            try container.encode("offer", forKey: .type)
            try container.encode(sdp, forKey: .sdp)
            try container.encode(clientId, forKey: .clientId)
        case .answer(let sdp, let clientId):
            try container.encode("answer", forKey: .type)
            try container.encode(sdp, forKey: .sdp)
            try container.encode(clientId, forKey: .clientId)
        case .ice(let candidate, let sdpMid, let sdpMLineIndex, let clientId):
            try container.encode("ice", forKey: .type)
            try container.encode(candidate, forKey: .candidate)
            try container.encode(sdpMid, forKey: .sdpMid)
            try container.encode(sdpMLineIndex, forKey: .sdpMLineIndex)
            try container.encode(clientId, forKey: .clientId)
        }
    }

    func jsonData() -> Data? {
        try? JSONEncoder().encode(self)
    }

    static func from(data: Data) -> SignalingMessage? {
        try? JSONDecoder().decode(SignalingMessage.self, from: data)
    }
}
