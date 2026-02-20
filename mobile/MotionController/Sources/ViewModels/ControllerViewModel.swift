import Foundation
import Combine

@MainActor
final class ControllerViewModel: ObservableObject {
    @Published var currentData: SensorData?
    @Published var isSending = false
    @Published var sendCount: Int = 0

    let motionService = MotionService()
    private weak var signalingService: SignalingService?
    private var cancellable: AnyCancellable?
    private var playerId: Int = 1

    func bind(signalingService: SignalingService, playerId: Int = 1) {
        self.signalingService = signalingService
        self.playerId = playerId
    }

    func startStreaming() {
        motionService.start()
        isSending = true

        cancellable = motionService.$currentData
            .compactMap { $0 }
            .sink { [weak self] data in
                guard let self else { return }
                let tagged = SensorData(
                    acceleration: data.acceleration,
                    rotation: data.rotation,
                    calibrated: data.calibrated,
                    playerId: self.playerId
                )
                self.currentData = tagged
                if let jsonData = tagged.jsonData() {
                    self.signalingService?.sendRawData(jsonData)
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
