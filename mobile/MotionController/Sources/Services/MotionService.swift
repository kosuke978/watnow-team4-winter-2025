import Foundation
import CoreMotion
import Combine

final class MotionService: ObservableObject {
    private let motionManager = CMMotionManager()
    private let queue = OperationQueue()

    @Published var currentData: SensorData?
    @Published var isAvailable = false

    private var calibrationAcceleration: Vector3 = .zero
    private var calibrationRotation: Rotation = .zero
    private var isCalibrated = false

    init() {
        queue.name = "com.watnow.team4.motion"
        queue.maxConcurrentOperationCount = 1
        isAvailable = motionManager.isDeviceMotionAvailable
    }

    func start() {
        guard motionManager.isDeviceMotionAvailable else {
            isAvailable = false
            return
        }

        motionManager.deviceMotionUpdateInterval = Constants.sensorUpdateInterval

        motionManager.startDeviceMotionUpdates(
            using: .xArbitraryZVertical,
            to: queue
        ) { [weak self] motion, error in
            guard let self, let motion, error == nil else { return }

            let rawAcceleration = Vector3(
                x: motion.userAcceleration.x * 9.81,
                y: motion.userAcceleration.y * 9.81,
                z: motion.userAcceleration.z * 9.81
            )
            let rawRotation = Rotation(
                pitch: motion.attitude.pitch,
                roll: motion.attitude.roll,
                yaw: motion.attitude.yaw
            )

            let acceleration: Vector3
            let rotation: Rotation

            if self.isCalibrated {
                acceleration = rawAcceleration - self.calibrationAcceleration
                rotation = rawRotation - self.calibrationRotation
            } else {
                acceleration = rawAcceleration
                rotation = rawRotation
            }

            let data = SensorData(
                acceleration: acceleration,
                rotation: rotation,
                calibrated: self.isCalibrated
            )

            DispatchQueue.main.async {
                self.currentData = data
            }
        }
    }

    func stop() {
        motionManager.stopDeviceMotionUpdates()
        DispatchQueue.main.async {
            self.currentData = nil
        }
    }

    func calibrate() {
        guard let motion = motionManager.deviceMotion else { return }

        calibrationAcceleration = Vector3(
            x: motion.userAcceleration.x * 9.81,
            y: motion.userAcceleration.y * 9.81,
            z: motion.userAcceleration.z * 9.81
        )
        calibrationRotation = Rotation(
            pitch: motion.attitude.pitch,
            roll: motion.attitude.roll,
            yaw: motion.attitude.yaw
        )
        isCalibrated = true
    }

    func resetCalibration() {
        calibrationAcceleration = .zero
        calibrationRotation = .zero
        isCalibrated = false
    }

    deinit {
        stop()
    }
}
