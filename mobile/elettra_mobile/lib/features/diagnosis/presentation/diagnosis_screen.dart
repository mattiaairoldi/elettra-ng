import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../problems/data/problem_models.dart';
import '../../problems/data/problems_repository.dart';
import '../../shell/data/shell_navigation.dart';

class DiagnosisScreen extends ConsumerStatefulWidget {
  const DiagnosisScreen({super.key});

  @override
  ConsumerState<DiagnosisScreen> createState() => _DiagnosisScreenState();
}

class _DiagnosisScreenState extends ConsumerState<DiagnosisScreen> {
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  int? _selectedChapterId;
  int? _selectedOptionId;
  var _submitting = false;
  String? _error;

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final chapters = ref.watch(diagnosticChaptersProvider(null));

    return chapters.when(
      data: (items) {
        if (items.isEmpty) {
          return const _EmptyDiagnosis();
        }

        final selectedChapter = _selectedChapter(items);
        return Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _PanelTitle(
                  icon: Icons.forum_outlined,
                  label: 'Nuova diagnosi',
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<int>(
                  initialValue: selectedChapter.id,
                  decoration: const InputDecoration(
                    labelText: 'Area diagnostica',
                    prefixIcon: Icon(Icons.category_outlined),
                  ),
                  items: [
                    for (final chapter in items)
                      DropdownMenuItem(
                        value: chapter.id,
                        child: Text(chapter.name),
                      ),
                  ],
                  onChanged: _submitting
                      ? null
                      : (value) => setState(() {
                          _selectedChapterId = value;
                          _selectedOptionId = null;
                          _error = null;
                        }),
                ),
                if (selectedChapter.description.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(selectedChapter.description),
                ],
                if (selectedChapter.options.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  Text(
                    'Scenario',
                    style: Theme.of(context).textTheme.labelLarge,
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (final option in selectedChapter.options)
                        ChoiceChip(
                          label: Text(option.label),
                          selected: _selectedOptionId == option.id,
                          onSelected: _submitting
                              ? null
                              : (selected) => setState(() {
                                  _selectedOptionId = selected
                                      ? option.id
                                      : null;
                                  _error = null;
                                }),
                        ),
                    ],
                  ),
                ],
                const SizedBox(height: 14),
                TextField(
                  controller: _titleController,
                  enabled: !_submitting,
                  decoration: InputDecoration(
                    labelText: 'Titolo',
                    hintText: 'Diagnosi: ${selectedChapter.name}',
                    prefixIcon: const Icon(Icons.title),
                  ),
                  textInputAction: TextInputAction.next,
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _descriptionController,
                  enabled: !_submitting,
                  decoration: const InputDecoration(
                    labelText: 'Descrizione',
                    prefixIcon: Icon(Icons.notes_outlined),
                  ),
                  minLines: 4,
                  maxLines: 7,
                ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    _error!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                ],
                const SizedBox(height: 16),
                FilledButton.icon(
                  onPressed: _submitting
                      ? null
                      : () => _submitDiagnosis(selectedChapter),
                  icon: _submitting
                      ? const SizedBox.square(
                          dimension: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.play_arrow_outlined),
                  label: const Text('Avvia diagnosi'),
                ),
              ],
            ),
          ),
        );
      },
      error: (error, stackTrace) => _DiagnosisError(
        onRetry: () => ref.invalidate(diagnosticChaptersProvider(null)),
      ),
      loading: () => const Padding(
        padding: EdgeInsets.symmetric(vertical: 32),
        child: Center(child: CircularProgressIndicator()),
      ),
    );
  }

  DiagnosticChapter _selectedChapter(List<DiagnosticChapter> chapters) {
    final selectedId = _selectedChapterId;
    if (selectedId != null) {
      for (final chapter in chapters) {
        if (chapter.id == selectedId) {
          return chapter;
        }
      }
    }
    return chapters.first;
  }

  DiagnosticChapterOption? _selectedOption(DiagnosticChapter chapter) {
    final selectedId = _selectedOptionId;
    if (selectedId == null) {
      return null;
    }
    for (final option in chapter.options) {
      if (option.id == selectedId) {
        return option;
      }
    }
    return null;
  }

  Future<void> _submitDiagnosis(DiagnosticChapter chapter) async {
    if (_submitting) {
      return;
    }

    final categoryId = chapter.categoryId;
    final description = _descriptionController.text.trim();
    final title = _titleController.text.trim().isEmpty
        ? 'Diagnosi: ${chapter.name}'
        : _titleController.text.trim();

    if (categoryId == null || categoryId <= 0) {
      setState(
        () => _error = 'Area diagnostica non collegata a una categoria.',
      );
      return;
    }
    if (description.isEmpty) {
      setState(() => _error = 'Descrivi il problema per avviare la diagnosi.');
      return;
    }

    setState(() {
      _submitting = true;
      _error = null;
    });

    CustomerProblem? createdProblem;
    try {
      final repository = ref.read(problemsRepositoryProvider);
      createdProblem = await repository.createProblemFromDiagnosis(
        categoryId: categoryId,
        title: title,
        description: description,
        priority: 'normal',
      );
      final session = await repository.createAiSession(
        caseId: createdProblem.id,
      );
      final turnResult = await repository.sendDiagnosticTurn(
        sessionId: session.id,
        content: description,
        chapterId: chapter.id,
        optionId: _selectedOption(chapter)?.id,
      );
      _openProblem(
        createdProblem.id,
        aiSession: session,
        aiMessages: [turnResult.userMessage, turnResult.assistantMessage],
        aiSnapshot: turnResult.snapshot,
      );
    } catch (_) {
      if (!mounted) {
        return;
      }
      if (createdProblem != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Pratica aperta. Diagnosi AI non completata.'),
          ),
        );
        _openProblem(createdProblem.id);
        return;
      }
      setState(() => _error = 'Diagnosi non avviata.');
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }

  void _openProblem(
    int problemId, {
    AiSessionSummary? aiSession,
    List<AiMessage> aiMessages = const [],
    AiDiagnosticSnapshot? aiSnapshot,
  }) {
    ref.invalidate(problemsProvider);
    ref
        .read(shellNavigationProvider.notifier)
        .openProblems(
          problemId: problemId,
          aiSession: aiSession,
          aiMessages: aiMessages,
          aiSnapshot: aiSnapshot,
        );
  }
}

class _PanelTitle extends StatelessWidget {
  const _PanelTitle({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: Theme.of(context).colorScheme.primary),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            label,
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
          ),
        ),
      ],
    );
  }
}

class _EmptyDiagnosis extends StatelessWidget {
  const _EmptyDiagnosis();

  @override
  Widget build(BuildContext context) {
    return const Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(Icons.forum_outlined),
            SizedBox(width: 12),
            Expanded(child: Text('Nessuna diagnosi guidata disponibile.')),
          ],
        ),
      ),
    );
  }
}

class _DiagnosisError extends StatelessWidget {
  const _DiagnosisError({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(Icons.error_outline, color: scheme.error),
            const SizedBox(width: 12),
            const Expanded(child: Text('Diagnosi non caricata.')),
            IconButton(
              tooltip: 'Riprova',
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
            ),
          ],
        ),
      ),
    );
  }
}
