import 'package:flutter_riverpod/flutter_riverpod.dart';

class ShellNavigationState {
  const ShellNavigationState({
    this.selectedIndex = ShellDestinationIndex.home,
    this.problemId,
    this.revision = 0,
  });

  final int selectedIndex;
  final int? problemId;
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

  void openProblems({int? problemId}) {
    state = ShellNavigationState(
      selectedIndex: ShellDestinationIndex.problems,
      problemId: problemId,
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
