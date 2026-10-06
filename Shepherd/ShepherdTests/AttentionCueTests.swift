import Testing
@testable import Shepherd

struct AttentionCueTests {
    private let claude = SessionIdentity(
        paneID: "w1:p1", terminalID: "term_a", workspaceID: "w1", tabID: "w1:t1",
        agent: "claude", agentSession: "sess-a"
    )
    private let codex = SessionIdentity(
        paneID: "w1:p2", terminalID: "term_b", workspaceID: "w1", tabID: "w1:t1",
        agent: "codex", agentSession: "sess-b"
    )

    private final class Recorder {
        var cues: [AttentionCue] = []
    }

    private func director() throws -> (CompanionDirector, Recorder) {
        let behavior = CompanionBehavior(catalog: try AnimationCatalog.bundled(.block), startedAt: 0)
        let director = CompanionDirector(behavior: behavior, startedAt: 0)
        let recorder = Recorder()
        director.onAttention = { recorder.cues.append($0) }
        return (director, recorder)
    }

    @Test func onlyTheHopAndTheWaveCallForAttention() {
        #expect(CompanionAnimation.allCases.compactMap(AttentionCue.init) == [.finished, .needsYou])
    }

    @Test func finishingSparklesOnce() throws {
        let (director, recorder) = try director()
        director.apply(.connected([.init(identity: claude, status: .working)]), at: 0)

        director.apply(.statusChanged(paneID: claude.paneID, status: .ready), at: 1)
        director.apply(.statusChanged(paneID: claude.paneID, status: .ready), at: 2)

        #expect(recorder.cues == [.finished])
    }

    @Test func waitingForYouSparklesWhenTheWaveStarts() throws {
        let (director, recorder) = try director()
        director.apply(.connected([
            .init(identity: claude, status: .working),
            .init(identity: codex, status: .working),
        ]), at: 0)

        director.apply(.statusChanged(paneID: claude.paneID, status: .needsYou), at: 1)
        director.apply(.statusChanged(paneID: codex.paneID, status: .needsYou), at: 2)

        #expect(recorder.cues == [.needsYou])
    }

    @Test func aCompletionHiddenBehindAQuestionDoesNotSparkle() throws {
        let (director, recorder) = try director()
        director.apply(.connected([
            .init(identity: claude, status: .working),
            .init(identity: codex, status: .needsYou),
        ]), at: 0)
        recorder.cues = []

        director.apply(.statusChanged(paneID: claude.paneID, status: .ready), at: 1)

        #expect(recorder.cues.isEmpty)
    }

    @Test func quietSnapshotsAndWorkDoNotSparkle() throws {
        let (director, recorder) = try director()

        director.apply(.connected([.init(identity: claude, status: .ready)]), at: 0)
        director.apply(.statusChanged(paneID: claude.paneID, status: .working), at: 1)
        director.apply(.disconnected, at: 2)

        #expect(recorder.cues.isEmpty)
    }
}
