import AppKit
import QuartzCore

/// A click-through window around Shepherd that sparkles bursts out from. It is
/// a child of his panel so it follows every drag and screen change, and it is
/// larger than him because his own panel is exactly his size and would clip
/// anything flying outward.
final class SparkleOverlay {
    static let margin: CGFloat = 570

    private let window: NSPanel
    private let host = NSView()

    init() {
        window = NSPanel(
            contentRect: .zero,
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )
        window.level = .floating
        window.collectionBehavior = [.moveToActiveSpace, .ignoresCycle]
        window.isOpaque = false
        window.backgroundColor = .clear
        window.hasShadow = false
        window.ignoresMouseEvents = true
        window.animationBehavior = .none
        window.isReleasedWhenClosed = false

        host.wantsLayer = true
        window.contentView = host
    }

    func attach(to panel: NSPanel) {
        window.setFrame(panel.frame.insetBy(dx: -Self.margin, dy: -Self.margin), display: false)
        if window.parent !== panel {
            panel.addChildWindow(window, ordered: .above)
        }
    }

    /// Bursts once around the companion; the emitter is removed after its
    /// last particle fades so nothing animates while he is quiet.
    func burst(_ cue: AttentionCue) {
        guard let root = host.layer else { return }

        let style = SparkleStyle(cue)
        let emitter = CAEmitterLayer()
        emitter.frame = root.bounds
        emitter.contentsScale = window.backingScaleFactor
        emitter.emitterPosition = CGPoint(x: root.bounds.midX, y: root.bounds.midY)
        emitter.emitterShape = .circle
        emitter.emitterMode = .outline
        emitter.emitterSize = CGSize(width: 96, height: 96)
        emitter.renderMode = .oldestLast
        emitter.emitterCells = style.cells
        // Without this the emitter would be simulated from time zero and
        // start mid-flight instead of from Shepherd's outline.
        emitter.beginTime = CACurrentMediaTime()
        root.addSublayer(emitter)

        DispatchQueue.main.asyncAfter(deadline: .now() + style.emitFor) {
            emitter.birthRate = 0
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + style.emitFor + style.lifetime) {
            emitter.removeFromSuperlayer()
        }
    }
}

private struct SparkleStyle {
    let cells: [CAEmitterCell]
    let emitFor: TimeInterval
    let lifetime: TimeInterval

    /// Catppuccin Mocha, the palette Ram is drawn in: warm yellow and green
    /// for a finished response, peach, pink and mauve for a waiting agent.
    init(_ cue: AttentionCue) {
        let colors: [NSColor]
        switch cue {
        case .finished:
            colors = [.init(hex: 0xF9E2AF), .init(hex: 0xA6E3A1), .init(hex: 0xFFFFFF)]
            emitFor = 0.28
        case .needsYou:
            colors = [.init(hex: 0xFAB387), .init(hex: 0xF5C2E7), .init(hex: 0xCBA6F7)]
            emitFor = 0.5
        }
        let lifetime: Float = 1.7
        self.lifetime = TimeInterval(lifetime)

        let star = SparkleImage.star
        let dot = SparkleImage.dot
        cells = colors.flatMap { color in
            [Self.cell(image: star, color: color, birthRate: 26, scale: 0.9, lifetime: lifetime),
             Self.cell(image: dot, color: color, birthRate: 18, scale: 0.55, lifetime: lifetime * 0.7)]
        }
    }

    private static func cell(image: CGImage?, color: NSColor, birthRate: Float, scale: CGFloat, lifetime: Float) -> CAEmitterCell {
        let cell = CAEmitterCell()
        cell.contents = image
        cell.contentsScale = 2
        cell.color = color.cgColor
        cell.birthRate = birthRate
        cell.lifetime = lifetime
        cell.lifetimeRange = lifetime * 0.3
        cell.velocity = 225
        cell.velocityRange = 110
        cell.yAcceleration = -30
        cell.emissionRange = .pi * 2
        cell.scale = scale
        cell.scaleRange = scale * 0.5
        cell.scaleSpeed = -scale * 0.4
        cell.alphaSpeed = -1 / lifetime
        cell.spin = 2
        cell.spinRange = 4
        return cell
    }
}

/// Drawn in white so each emitter cell tints it with its own colour.
private enum SparkleImage {
    static let star = draw(size: 48) { context, rect in
        let c = CGPoint(x: rect.midX, y: rect.midY)
        let outer = rect.width / 2
        let inner = outer * 0.22
        let path = CGMutablePath()
        for index in 0..<8 {
            let angle = CGFloat(index) * .pi / 4 + .pi / 2
            let radius = index.isMultiple(of: 2) ? outer : inner
            let point = CGPoint(x: c.x + cos(angle) * radius, y: c.y + sin(angle) * radius)
            index == 0 ? path.move(to: point) : path.addLine(to: point)
        }
        path.closeSubpath()
        context.addPath(path)
        context.fillPath()
    }

    static let dot = draw(size: 20) { context, rect in
        context.fillEllipse(in: rect.insetBy(dx: 2, dy: 2))
    }

    private static func draw(size: Int, _ body: (CGContext, CGRect) -> Void) -> CGImage? {
        guard let context = CGContext(
            data: nil,
            width: size,
            height: size,
            bitsPerComponent: 8,
            bytesPerRow: 0,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else { return nil }
        context.setFillColor(.white)
        body(context, CGRect(x: 0, y: 0, width: size, height: size))
        return context.makeImage()
    }
}

private extension NSColor {
    convenience init(hex: UInt32) {
        self.init(
            srgbRed: CGFloat((hex >> 16) & 0xFF) / 255,
            green: CGFloat((hex >> 8) & 0xFF) / 255,
            blue: CGFloat(hex & 0xFF) / 255,
            alpha: 1
        )
    }
}
