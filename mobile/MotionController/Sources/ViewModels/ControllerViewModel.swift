import Foundation
import Combine

@MainActor
final class ControllerViewModel: ObservableObject {
    @Published var currentData: SensorData?
    @Published var isSending = false
    @Published var sendCount: Int = 0

    let motionService = MotionService()
    private weak var webRTCService: WebRTCService?
    private var cancellable: AnyCancellable?

    func bind(webRTCService: WebRTCService) {
        self.webRTCService = webRTCService
    }

    func startStreaming() {
        motionService.start()
        isSending = true

        cancellable = motionService.$currentData
            .compactMap { $0 }
            .sink { [weak self] data in
                guard let self else { return }
                self.currentData = data
                if let jsonData = data.jsonData() {
                    self.webRTCService?.sendData(jsonData)
                    self.sendCount += 1
                }
            }
    }

    func stopStreaming() {
        cancellable?.cancel()
        cancellable = nil
        motionService.stop()
        isSending = false
    }

    func calibrate() {
        motionService.calibrate()
    }

    func resetCalibration() {
        motionService.resetCalibration()
    }
}
