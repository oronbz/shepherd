import Testing
import CoreGraphics
@testable import Shepherd

struct SparkleOverlayTests {
    private let screen = CGRect(x: 0, y: 0, width: 1440, height: 900)
    private let companion = CGRect(x: 640, y: 380, width: 128, height: 128)

    @Test func inMidScreenTheSparklesCentreOnHim() {
        let placement = SparkleOverlay.placement(around: companion, on: screen)

        #expect(placement.frame.midX == companion.midX)
        #expect(placement.frame.origin + placement.center == CGPoint(x: companion.midX, y: companion.midY))
    }

    @Test func nearTheTopTheSparklesStillCentreOnHim() {
        let companion = CGRect(x: 1288, y: 748, width: 128, height: 128)

        let placement = SparkleOverlay.placement(around: companion, on: screen)

        #expect(screen.contains(placement.frame))
        #expect(placement.frame.origin + placement.center == CGPoint(x: companion.midX, y: companion.midY))
    }

    @Test func theOverlayNeverReachesOntoTheNextDisplay() {
        let companion = CGRect(x: 24, y: 24, width: 128, height: 128)

        let placement = SparkleOverlay.placement(around: companion, on: screen)

        #expect(placement.frame.minX == screen.minX)
        #expect(placement.frame.origin + placement.center == CGPoint(x: companion.midX, y: companion.midY))
    }
}

private extension CGPoint {
    static func + (lhs: CGPoint, rhs: CGPoint) -> CGPoint {
        CGPoint(x: lhs.x + rhs.x, y: lhs.y + rhs.y)
    }
}
