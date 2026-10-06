import Foundation

final class CompanionDirector {
    private let model = ActivityModel()
    private let behavior: CompanionBehavior
    private var shown: CompanionAnimation
    private var celebrating: SessionIdentity?
    private var waiting: SessionIdentity?

    /// Called with each wave and hop the director starts, after Shepherd shows it.
    var onAttention: (AttentionCue) -> Void = { _ in }

    init(behavior: CompanionBehavior, startedAt now: TimeInterval) {
        self.behavior = behavior
        shown = model.state
        behavior.show(shown, at: now)
    }

    var sessions: [SessionRecord] { model.sessions }

    func apply(_ event: ActivityEvent, at now: TimeInterval) {
        let update = model.apply(event)
        waiting = update.state == .needsYou ? model.waitingSession(preferring: waiting) : nil

        if update.state != shown {
            behavior.show(update.state, at: now)
            shown = update.state
            if update.state == .needsYou { onAttention(.needsYou) }
        }
        if let finished = update.finished.last, update.state != .needsYou {
            behavior.show(.finished, at: now)
            celebrating = finished
            onAttention(.finished)
        }
    }

    /// Resolved at click time against the sessions Herdr currently reports, so
    /// a hop whose session has since closed or changed occupant targets nothing
    /// rather than whichever session happens to remain.
    func clickTarget(at now: TimeInterval) -> SessionIdentity? {
        let hopping = behavior.isPlaying(.finished, at: now)
        return model.navigationTarget(waiting: waiting, celebrating: hopping ? celebrating : nil)
    }

    func reactPlayfully(at now: TimeInterval) {
        behavior.reactPlayfully(at: now)
    }
}
