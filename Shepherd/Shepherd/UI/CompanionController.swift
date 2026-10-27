import AppKit

final class CompanionController {
    private let behavior: CompanionBehavior
    private let director: CompanionDirector
    private var navigator: ClickNavigator?
    private let panel: CompanionPanel
    private let spriteView: SpriteView
    private let positions: CompanionPositionStore
    private let sparkles: SparklePreferenceStore
    private let sparkleOverlay = SparkleOverlay()
    private var frameTimer: Timer?

    private var now: TimeInterval { ProcessInfo.processInfo.systemUptime }

    init(
        avatar: CompanionAvatar,
        positions: CompanionPositionStore = CompanionPositionStore(),
        sparkles: SparklePreferenceStore = SparklePreferenceStore()
    ) {
        self.positions = positions
        self.sparkles = sparkles
        let startedAt = ProcessInfo.processInfo.systemUptime
        behavior = CompanionBehavior(catalog: avatar.catalog, startedAt: startedAt)
        director = CompanionDirector(behavior: behavior, startedAt: startedAt)

        let size = avatar.catalog.desktopSize
        panel = CompanionPanel(size: size)
        spriteView = SpriteView(avatar: avatar)
        panel.contentView = spriteView

        spriteView.onHoverChange = { [weak self] isHovering in
            guard let self else { return }
            behavior.setHovering(isHovering, at: now)
            render()
        }
        spriteView.onMove = { [weak self] origin in
            self?.panel.setFrameOrigin(origin)
        }
        spriteView.onDragEnd = { [weak self] in
            self?.positions.savedOrigin = self?.panel.frame.origin
        }
        spriteView.onClick = { [weak self] in
            self?.click()
        }
        director.onAttention = { [weak self] cue in
            self?.sparkle(cue)
        }

        panel.setFrameOrigin(
            CompanionPlacement.origin(saved: positions.savedOrigin, size: size, visibleFrames: visibleFrames)
        )

        NotificationCenter.default.addObserver(
            self,
            selector: #selector(screenParametersChanged),
            name: NSApplication.didChangeScreenParametersNotification,
            object: nil
        )
    }

    func attach(_ menu: NSMenu) {
        spriteView.menu = menu
    }

    func show() {
        panel.orderFrontRegardless()
        sparkleOverlay.attach(to: panel)
        render()
    }

    func use(_ avatar: CompanionAvatar) {
        behavior.use(avatar.catalog)
        spriteView.use(avatar)
        render()
    }

    func show(_ animation: CompanionAnimation) {
        behavior.show(animation, at: now)
        render()
        AttentionCue(animation).map(sparkle)
    }

    func apply(_ event: ActivityEvent) {
        director.apply(event, at: now)
        render()
    }

    func navigate(through host: NavigationHost) {
        let navigator = ClickNavigator(director: director, host: host)
        navigator.onOutcome = { [weak self] outcome in
            #if DEBUG
            NSLog("Shepherd navigation: \(outcome)")
            #endif
            self?.render()
        }
        self.navigator = navigator
    }

    func click() {
        navigator?.click(at: now)
    }

    /// Sparkles are skipped when turned off from his menu, and when the user
    /// asks macOS to reduce motion.
    private func sparkle(_ cue: AttentionCue) {
        guard sparkles.isEnabled, !NSWorkspace.shared.accessibilityDisplayShouldReduceMotion else { return }
        sparkleOverlay.burst(cue)
    }

    private func render() {
        let presentation = behavior.presentation(at: now)
        spriteView.show(presentation)
        scheduleNextFrame()
    }

    private func scheduleNextFrame() {
        frameTimer?.invalidate()
        frameTimer = nil

        guard panel.isVisible, let delay = behavior.timeUntilNextFrame(at: now) else { return }

        let timer = Timer(timeInterval: max(delay, 1.0 / 60), repeats: false) { [weak self] _ in
            self?.render()
        }
        // Dragging Shepherd and opening his menu both run the event-tracking
        // run loop mode, where a default-mode timer would stall his animation.
        RunLoop.main.add(timer, forMode: .common)
        frameTimer = timer
    }

    private var visibleFrames: [CGRect] {
        NSScreen.screens.map(\.visibleFrame)
    }

    @objc private func screenParametersChanged() {
        let origin = CompanionPlacement.origin(
            saved: panel.frame.origin,
            size: panel.frame.size,
            visibleFrames: visibleFrames
        )
        panel.setFrameOrigin(origin)
        positions.savedOrigin = origin
    }
}
