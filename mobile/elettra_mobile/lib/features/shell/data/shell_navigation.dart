import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../problems/data/problem_models.dart';

class ShellNavigationState {
  const ShellNavigationState({
    this.selectedIndex = ShellDestinationIndex.home,
    this.problemId,
    this.aiSession,
    this.aiMessages = const [],
    this.aiSnapshot,
    this.revision = 0,
  });

  final int selectedIndex;
  final int? problemId;
  final AiSessionSummary? aiSession;
  final List<AiMessage> aiMessages;
  final AiDiagnosticSnapshot? aiSnapshot;
  final int revision;
}

class ShellDestinationIndex {
  const ShellDestinationIndex._();

  static const home = 0;
  static const problems = 1;
  static const diagnosis = 2;
}

class ShellNavigationNotifier extends Notifier<ShellNavigationState> {
  @override
  ShellNavigationState build() => const ShellNavigationState();

  void selectIndex(int index) {
    state = ShellNavigationState(
      selectedIndex: index,
      revision: state.revision + 1,
    );
  }

  void openHome() {
    selectIndex(ShellDestinationIndex.home);
  }

  void openProblems({
    int? problemId,
    AiSessionSummary? aiSession,
    List<AiMessage> aiMessages = const [],
    AiDiagnosticSnapshot? aiSnapshot,
  }) {
    state = ShellNavigationState(
      selectedIndex: ShellDestinationIndex.problems,
      problemId: problemId,
      aiSession: aiSession,
      aiMessages: aiMessages,
      aiSnapshot: aiSnapshot,
      revision: state.revision + 1,
    );
  }

  void openDiagnosis() {
    selectIndex(ShellDestinationIndex.diagnosis);
  }
}

final shellNavigationProvider =
    NotifierProvider<ShellNavigationNotifier, ShellNavigationState>(
      ShellNavigationNotifier.new,
    );
