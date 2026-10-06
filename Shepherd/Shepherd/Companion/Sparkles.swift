import Foundation

/// The reactions that ask for the user's eye, and so get a burst of sparkles
/// around Shepherd: the hop when a response ends and the wave when an agent
/// waits for you.
enum AttentionCue: Equatable, Sendable {
    case finished
    case needsYou

    init?(_ animation: CompanionAnimation) {
        switch animation {
        case .finished: self = .finished
        case .needsYou: self = .needsYou
        default: return nil
        }
    }
}

final class SparklePreferenceStore {
    private static let key = "sparkles"
    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
    }

    var isEnabled: Bool {
        get { defaults.object(forKey: Self.key) as? Bool ?? true }
        set { defaults.set(newValue, forKey: Self.key) }
    }
}
