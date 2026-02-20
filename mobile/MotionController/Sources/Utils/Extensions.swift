import Foundation
import WebRTC

extension RTCSessionDescription {
    var jsonDictionary: [String: Any] {
        [
            "type": RTCSessionDescription.string(for: type),
            "sdp": sdp
        ]
    }
}

extension RTCIceCandidate {
    var jsonDictionary: [String: Any] {
        [
            "candidate": sdp,
            "sdpMid": sdpMid ?? "",
            "sdpMLineIndex": sdpMLineIndex
        ]
    }
}

extension String {
    func toRTCSessionDescription(type: RTCSdpType) -> RTCSessionDescription {
        RTCSessionDescription(type: type, sdp: self)
    }
}
