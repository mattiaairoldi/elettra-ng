import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/i18n/diagnostic_labels.dart';
import '../../shell/data/shell_navigation.dart';
import '../data/problem_models.dart';
import '../data/problems_repository.dart';

class ProblemsScreen extends ConsumerStatefulWidget {
  const ProblemsScreen({
    super.key,
    this.initialProblemId,
    this.initialAiSession,
    this.initialAiMessages = const [],
    this.initialAiSnapshot,
    this.navigationRevision = 0,
  });

  final int? initialProblemId;
  final AiSessionSummary? initialAiSession;
  final List<AiMessage> initialAiMessages;
  final AiDiagnosticSnapshot? initialAiSnapshot;
  final int navigationRevision;

  @override
  ConsumerState<ProblemsScreen> createState() => _ProblemsScreenState();
}

class _ProblemsScreenState extends ConsumerState<ProblemsScreen> {
  CustomerProblem? _selectedProblem;
  AiSessionSummary? _initialAiSession;
  List<AiMessage> _initialAiMessages = const [];
  AiDiagnosticSnapshot? _initialAiSnapshot;
  int _handledNavigationRevision = -1;

  @override
  Widget build(BuildContext context) {
    final problems = ref.watch(problemsProvider);

    return problems.when(
      data: (items) {
        _applyNavigationRequest(items);
        final selected = _selectedProblem;
        if (selected != null) {
          final current =
              items.where((item) => item.id == selected.id).firstOrNull ??
              selected;
          return _ProblemDetail(
            problem: current,
            initialAiSession: _initialAiSession,
            initialAiMessages: _initialAiMessages,
            initialAiSnapshot: _initialAiSnapshot,
            onBack: () => setState(() => _selectedProblem = null),
          );
        }

        if (items.isEmpty) {
          return const _EmptyProblems();
        }

        return Column(
          children: [
            for (final problem in items) ...[
              _ProblemCard(
                problem: problem,
                onOpen: () => setState(() {
                  _selectedProblem = problem;
                  _initialAiSession = null;
                  _initialAiMessages = const [];
                  _initialAiSnapshot = null;
                }),
              ),
              const SizedBox(height: 8),
            ],
          ],
        );
      },
      error: (error, stackTrace) =>
          _ProblemsError(onRetry: () => ref.invalidate(problemsProvider)),
      loading: () => const Padding(
        padding: EdgeInsets.symmetric(vertical: 32),
        child: Center(child: CircularProgressIndicator()),
      ),
    );
  }

  void _applyNavigationRequest(List<CustomerProblem> items) {
    if (_handledNavigationRevision == widget.navigationRevision) {
      return;
    }
    _handledNavigationRevision = widget.navigationRevision;
    final problemId = widget.initialProblemId;
    if (problemId == null) {
      _selectedProblem = null;
      _initialAiSession = null;
      _initialAiMessages = const [];
      _initialAiSnapshot = null;
      return;
    }
    _selectedProblem = items.where((item) => item.id == problemId).firstOrNull;
    _initialAiSession = widget.initialAiSession;
    _initialAiMessages = widget.initialAiMessages;
    _initialAiSnapshot = widget.initialAiSnapshot;
  }
}

class _ProblemDetail extends ConsumerStatefulWidget {
  const _ProblemDetail({
    required this.problem,
    required this.initialAiSession,
    required this.initialAiMessages,
    required this.initialAiSnapshot,
    required this.onBack,
  });

  final CustomerProblem problem;
  final AiSessionSummary? initialAiSession;
  final List<AiMessage> initialAiMessages;
  final AiDiagnosticSnapshot? initialAiSnapshot;
  final VoidCallback onBack;

  @override
  ConsumerState<_ProblemDetail> createState() => _ProblemDetailState();
}

class _ProblemDetailState extends ConsumerState<_ProblemDetail> {
  final _aiController = TextEditingController();
  int? _selectedChapterId;
  int? _selectedOptionId;
  AiSessionSummary? _aiSession;
  List<AiMessage> _aiMessages = const [];
  AiDiagnosticSnapshot? _snapshot;
  CaseShareRequestSummary? _shareRequest;
  var _sendingFeedback = false;
  var _sendingAi = false;
  var _sharing = false;

  @override
  void initState() {
    super.initState();
    _applyInitialAiContext();
  }

  @override
  void didUpdateWidget(covariant _ProblemDetail oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.problem.id != widget.problem.id ||
        oldWidget.initialAiSession?.id != widget.initialAiSession?.id) {
      _applyInitialAiContext();
    }
  }

  @override
  void dispose() {
    _aiController.dispose();
    super.dispose();
  }

  void _applyInitialAiContext() {
    _aiSession = widget.initialAiSession;
    _aiMessages = widget.initialAiMessages;
    _snapshot = widget.initialAiSnapshot;
  }

  @override
  Widget build(BuildContext context) {
    final chapters = ref.watch(
      diagnosticChaptersProvider(widget.problem.categoryId),
    );
    final professionals = ref.watch(
      professionalsProvider(widget.problem.categoryId),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextButton.icon(
          onPressed: widget.onBack,
          icon: const Icon(Icons.arrow_back),
          label: const Text('Problemi'),
        ),
        const SizedBox(height: 8),
        _ProblemSummaryCard(problem: widget.problem),
        const SizedBox(height: 12),
        chapters.when(
          data: (items) => _DiagnosticPanel(
            problem: widget.problem,
            chapters: items,
            selectedChapterId: _selectedChapterId,
            selectedOptionId: _selectedOptionId,
            sendingFeedback: _sendingFeedback,
            onChapterChanged: (chapterId) {
              setState(() {
                _selectedChapterId = chapterId;
                _selectedOptionId = null;
              });
            },
            onOptionChanged: (optionId) =>
                setState(() => _selectedOptionId = optionId),
            onFeedback: _sendAdviceFeedback,
          ),
          error: (error, stackTrace) => _InlineError(
            label: 'Diagnostica non caricata.',
            onRetry: () => ref.invalidate(
              diagnosticChaptersProvider(widget.problem.categoryId),
            ),
          ),
          loading: () => const _LoadingPanel(label: 'Diagnostica'),
        ),
        const SizedBox(height: 12),
        _AiDiagnosticPanel(
          controller: _aiController,
          messages: _aiMessages,
          snapshot: _snapshot,
          sending: _sendingAi,
          onSend: _sendAiTurn,
        ),
        const SizedBox(height: 12),
        professionals.when(
          data: (items) => _SharePanel(
            professionals: items,
            shareRequest: _shareRequest,
            sharing: _sharing,
            onShare: _shareCase,
          ),
          error: (error, stackTrace) => _InlineError(
            label: 'Professionisti non caricati.',
            onRetry: () => ref.invalidate(
              professionalsProvider(widget.problem.categoryId),
            ),
          ),
          loading: () => const _LoadingPanel(label: 'Tecnici disponibili'),
        ),
      ],
    );
  }

  Future<void> _sendAdviceFeedback(
    DiagnosticAdviceStep step,
    bool resolved,
  ) async {
    setState(() => _sendingFeedback = true);
    try {
      final result = await ref
          .read(problemsRepositoryProvider)
          .sendAdviceFeedback(
            stepId: step.id,
            caseId: widget.problem.id,
            resolved: resolved,
            note: '',
          );
      ref.invalidate(problemsProvider);
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(_feedbackMessage(result))));
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Feedback non salvato.')));
      }
    } finally {
      if (mounted) {
        setState(() => _sendingFeedback = false);
      }
    }
  }

  Future<void> _sendAiTurn() async {
    final content = _aiController.text.trim();
    if (content.isEmpty || _sendingAi) {
      return;
    }

    setState(() => _sendingAi = true);
    try {
      final repository = ref.read(problemsRepositoryProvider);
      final session =
          _aiSession ??
          await repository.createAiSession(caseId: widget.problem.id);
      final result = await repository.sendDiagnosticTurn(
        sessionId: session.id,
        content: content,
        chapterId: _selectedChapterId,
        optionId: _selectedOptionId,
      );
      final messages = await repository.fetchAiMessages(session.id);
      if (mounted) {
        setState(() {
          _aiSession = session;
          _aiMessages = messages;
          _snapshot = result.snapshot ?? _snapshot;
          _aiController.clear();
        });
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Turno AI non completato.')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _sendingAi = false);
      }
    }
  }

  Future<void> _shareCase(ProfessionalProfileSummary professional) async {
    if (_sharing) {
      return;
    }
    setState(() => _sharing = true);
    try {
      final shareRequest = await ref
          .read(problemsRepositoryProvider)
          .shareCase(
            caseId: widget.problem.id,
            professional: professional,
            title: widget.problem.title,
            summary: widget.problem.description,
          );
      if (mounted) {
        setState(() => _shareRequest = shareRequest);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Richiesta inviata a ${professional.displayName}.'),
          ),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Condivisione non riuscita.')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _sharing = false);
      }
    }
  }
}

class _ProblemCard extends StatelessWidget {
  const _ProblemCard({required this.problem, required this.onOpen});

  final CustomerProblem problem;
  final VoidCallback onOpen;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: onOpen,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Text(
                      problem.title,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  _StatusPill(label: _statusLabel(problem.status)),
                ],
              ),
              if (problem.description.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(
                  problem.description,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
              const SizedBox(height: 12),
              Row(
                children: [
                  Icon(
                    Icons.priority_high,
                    size: 18,
                    color: scheme.onSurfaceVariant,
                  ),
                  const SizedBox(width: 4),
                  Expanded(child: Text(_priorityLabel(problem.priority))),
                  const Icon(Icons.chevron_right),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ProblemSummaryCard extends StatelessWidget {
  const _ProblemSummaryCard({required this.problem});

  final CustomerProblem problem;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    problem.title,
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                _StatusPill(label: _statusLabel(problem.status)),
              ],
            ),
            if (problem.description.isNotEmpty) ...[
              const SizedBox(height: 10),
              Text(problem.description),
            ],
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _InfoChip(
                  icon: Icons.priority_high,
                  label: _priorityLabel(problem.priority),
                ),
                if (problem.assetId != null)
                  _InfoChip(
                    icon: Icons.inventory_2_outlined,
                    label: 'Asset ${problem.assetId}',
                  ),
                if (problem.propertyId != null)
                  _InfoChip(
                    icon: Icons.home_work_outlined,
                    label: 'Casa ${problem.propertyId}',
                  ),
              ],
            ),
            if (problem.status == 'resolved') ...[
              const SizedBox(height: 12),
              Text(
                'Caso risolto',
                style: Theme.of(
                  context,
                ).textTheme.labelLarge?.copyWith(color: scheme.primary),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _DiagnosticPanel extends StatelessWidget {
  const _DiagnosticPanel({
    required this.problem,
    required this.chapters,
    required this.selectedChapterId,
    required this.selectedOptionId,
    required this.sendingFeedback,
    required this.onChapterChanged,
    required this.onOptionChanged,
    required this.onFeedback,
  });

  final CustomerProblem problem;
  final List<DiagnosticChapter> chapters;
  final int? selectedChapterId;
  final int? selectedOptionId;
  final bool sendingFeedback;
  final ValueChanged<int?> onChapterChanged;
  final ValueChanged<int?> onOptionChanged;
  final Future<void> Function(DiagnosticAdviceStep step, bool resolved)
  onFeedback;

  @override
  Widget build(BuildContext context) {
    final chapter = _selectedChapter;
    final optionId = _selectedOptionId(chapter);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _PanelTitle(
              icon: Icons.checklist_outlined,
              label: 'Diagnostica guidata',
            ),
            const SizedBox(height: 12),
            if (chapters.isEmpty)
              const Text('Nessun capitolo diagnostico disponibile.')
            else ...[
              DropdownButtonFormField<int>(
                initialValue: chapter?.id,
                decoration: const InputDecoration(labelText: 'Capitolo'),
                items: [
                  for (final item in chapters)
                    DropdownMenuItem(value: item.id, child: Text(item.name)),
                ],
                onChanged: onChapterChanged,
              ),
              if (chapter != null && chapter.options.isNotEmpty) ...[
                const SizedBox(height: 12),
                DropdownButtonFormField<int?>(
                  initialValue: optionId,
                  decoration: const InputDecoration(labelText: 'Scenario'),
                  items: [
                    const DropdownMenuItem<int?>(
                      value: null,
                      child: Text('Generale'),
                    ),
                    for (final option in chapter.options)
                      DropdownMenuItem<int?>(
                        value: option.id,
                        child: Text(option.label),
                      ),
                  ],
                  onChanged: onOptionChanged,
                ),
              ],
              const SizedBox(height: 12),
              if (chapter != null)
                _AdviceStepsList(
                  chapterId: chapter.id,
                  optionId: optionId,
                  sendingFeedback: sendingFeedback,
                  onFeedback: onFeedback,
                ),
            ],
          ],
        ),
      ),
    );
  }

  DiagnosticChapter? get _selectedChapter {
    if (chapters.isEmpty) {
      return null;
    }
    for (final chapter in chapters) {
      if (chapter.id == selectedChapterId) {
        return chapter;
      }
    }
    return chapters.first;
  }

  int? _selectedOptionId(DiagnosticChapter? chapter) {
    if (chapter == null || selectedOptionId == null) {
      return null;
    }
    return chapter.options.any((option) => option.id == selectedOptionId)
        ? selectedOptionId
        : null;
  }
}

class _AdviceStepsList extends ConsumerWidget {
  const _AdviceStepsList({
    required this.chapterId,
    required this.optionId,
    required this.sendingFeedback,
    required this.onFeedback,
  });

  final int chapterId;
  final int? optionId;
  final bool sendingFeedback;
  final Future<void> Function(DiagnosticAdviceStep step, bool resolved)
  onFeedback;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FutureBuilder<List<DiagnosticAdviceStep>>(
      key: ValueKey('$chapterId-$optionId'),
      future: ref
          .read(problemsRepositoryProvider)
          .fetchAdviceSteps(chapterId: chapterId, optionId: optionId),
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Padding(
            padding: EdgeInsets.symmetric(vertical: 16),
            child: Center(child: CircularProgressIndicator()),
          );
        }
        if (snapshot.hasError) {
          return const Text('Consigli non caricati.');
        }
        final steps = snapshot.data ?? const [];
        if (steps.isEmpty) {
          return const Text('Nessun consiglio disponibile per lo scenario.');
        }
        return Column(
          children: [
            for (final step in steps.take(3)) ...[
              _AdviceStepTile(
                step: step,
                sendingFeedback: sendingFeedback,
                onFeedback: onFeedback,
              ),
              const SizedBox(height: 8),
            ],
          ],
        );
      },
    );
  }
}

class _AdviceStepTile extends StatelessWidget {
  const _AdviceStepTile({
    required this.step,
    required this.sendingFeedback,
    required this.onFeedback,
  });

  final DiagnosticAdviceStep step;
  final bool sendingFeedback;
  final Future<void> Function(DiagnosticAdviceStep step, bool resolved)
  onFeedback;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        border: Border.all(color: scheme.outlineVariant),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              step.title,
              style: Theme.of(
                context,
              ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700),
            ),
            if (step.body.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(step.body),
            ],
            if (step.resolutionPrompt.isNotEmpty) ...[
              const SizedBox(height: 10),
              Text(
                step.resolutionPrompt,
                style: Theme.of(context).textTheme.labelLarge,
              ),
            ],
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton.icon(
                  onPressed: sendingFeedback
                      ? null
                      : () => onFeedback(step, true),
                  icon: const Icon(Icons.check),
                  label: const Text('Risolto'),
                ),
                OutlinedButton.icon(
                  onPressed: sendingFeedback
                      ? null
                      : () => onFeedback(step, false),
                  icon: const Icon(Icons.arrow_forward),
                  label: const Text('Continua'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _AiDiagnosticPanel extends StatelessWidget {
  const _AiDiagnosticPanel({
    required this.controller,
    required this.messages,
    required this.snapshot,
    required this.sending,
    required this.onSend,
  });

  final TextEditingController controller;
  final List<AiMessage> messages;
  final AiDiagnosticSnapshot? snapshot;
  final bool sending;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) {
    final latestAssistant = messages
        .where((message) => message.role == 'assistant')
        .lastOrNull;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _PanelTitle(
              icon: Icons.forum_outlined,
              label: 'AI diagnostica',
            ),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              enabled: !sending,
              decoration: const InputDecoration(labelText: 'Aggiornamento'),
              minLines: 2,
              maxLines: 4,
            ),
            const SizedBox(height: 10),
            Align(
              alignment: Alignment.centerRight,
              child: FilledButton.icon(
                onPressed: sending ? null : onSend,
                icon: sending
                    ? const SizedBox.square(
                        dimension: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.send_outlined),
                label: const Text('Invia'),
              ),
            ),
            if (latestAssistant != null) ...[
              const SizedBox(height: 12),
              _AiMessageBox(message: latestAssistant),
            ],
            if (snapshot != null) ...[
              const SizedBox(height: 12),
              _SnapshotBox(snapshot: snapshot!),
            ],
          ],
        ),
      ),
    );
  }
}

class _AiMessageBox extends StatelessWidget {
  const _AiMessageBox({required this.message});

  final AiMessage message;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Text(
          message.content.isEmpty
              ? _messageStatus(message.status)
              : message.content,
        ),
      ),
    );
  }
}

class _SnapshotBox extends StatelessWidget {
  const _SnapshotBox({required this.snapshot});

  final AiDiagnosticSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (snapshot.summary.isNotEmpty)
          _SnapshotRow(label: 'Riepilogo', value: snapshot.summary),
        if (snapshot.riskLevel.isNotEmpty)
          _SnapshotRow(
            label: 'Rischio',
            value: diagnosticRiskLevelLabel(snapshot.riskLevel),
          ),
        if (snapshot.recommendation.isNotEmpty)
          _SnapshotRow(label: 'Indicazione', value: snapshot.recommendation),
        if (snapshot.nextQuestion.isNotEmpty)
          _SnapshotRow(label: 'Prossima domanda', value: snapshot.nextQuestion),
        if (snapshot.escalationRecommended)
          _SnapshotRow(
            label: 'Escalation',
            value: snapshot.escalationReason.isEmpty
                ? 'Consigliata'
                : snapshot.escalationReason,
          ),
      ],
    );
  }
}

class _SnapshotRow extends StatelessWidget {
  const _SnapshotRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: RichText(
        text: TextSpan(
          style: Theme.of(context).textTheme.bodyMedium,
          children: [
            TextSpan(
              text: '$label: ',
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            TextSpan(text: value),
          ],
        ),
      ),
    );
  }
}

class _SharePanel extends StatelessWidget {
  const _SharePanel({
    required this.professionals,
    required this.shareRequest,
    required this.sharing,
    required this.onShare,
  });

  final List<ProfessionalProfileSummary> professionals;
  final CaseShareRequestSummary? shareRequest;
  final bool sharing;
  final Future<void> Function(ProfessionalProfileSummary professional) onShare;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _PanelTitle(
              icon: Icons.engineering_outlined,
              label: 'Tecnici disponibili',
            ),
            if (shareRequest != null) ...[
              const SizedBox(height: 10),
              _InfoChip(
                icon: Icons.outgoing_mail,
                label: 'Richiesta ${_shareStatusLabel(shareRequest!.status)}',
              ),
            ],
            const SizedBox(height: 12),
            if (professionals.isEmpty)
              const Text('Nessun tecnico disponibile per questa categoria.')
            else
              Column(
                children: [
                  for (final professional in professionals.take(3)) ...[
                    _ProfessionalTile(
                      professional: professional,
                      sharing: sharing,
                      onShare: () => onShare(professional),
                    ),
                    const SizedBox(height: 8),
                  ],
                ],
              ),
          ],
        ),
      ),
    );
  }
}

class _ProfessionalTile extends StatelessWidget {
  const _ProfessionalTile({
    required this.professional,
    required this.sharing,
    required this.onShare,
  });

  final ProfessionalProfileSummary professional;
  final bool sharing;
  final VoidCallback onShare;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        border: Border.all(color: scheme.outlineVariant),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.engineering_outlined),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    professional.displayName,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  if (professional.serviceAreaText.isNotEmpty)
                    Text(professional.serviceAreaText),
                  if (professional.bio.isNotEmpty)
                    Text(
                      professional.bio,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              tooltip: 'Condividi',
              onPressed: sharing ? null : onShare,
              icon: const Icon(Icons.send_outlined),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: scheme.secondaryContainer,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        child: Text(
          label,
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
            color: scheme.onSecondaryContainer,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}

class _InfoChip extends StatelessWidget {
  const _InfoChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Chip(
      avatar: Icon(icon, size: 18),
      label: Text(label),
      visualDensity: VisualDensity.compact,
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
        Icon(icon),
        const SizedBox(width: 8),
        Text(
          label,
          style: Theme.of(
            context,
          ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
        ),
      ],
    );
  }
}

class _LoadingPanel extends StatelessWidget {
  const _LoadingPanel({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            const SizedBox.square(
              dimension: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            const SizedBox(width: 12),
            Text(label),
          ],
        ),
      ),
    );
  }
}

class _InlineError extends StatelessWidget {
  const _InlineError({required this.label, required this.onRetry});

  final String label;
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
            Expanded(child: Text(label)),
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

class _EmptyProblems extends ConsumerWidget {
  const _EmptyProblems();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.check_circle_outline, color: scheme.primary),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Nessun problema aperto',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Puoi partire dagli asset della casa oppure continuare con una diagnosi guidata.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton.icon(
                  onPressed: () =>
                      ref.read(shellNavigationProvider.notifier).openHome(),
                  icon: const Icon(Icons.home_work_outlined),
                  label: const Text('La mia casa'),
                ),
                OutlinedButton.icon(
                  onPressed: () => ref
                      .read(shellNavigationProvider.notifier)
                      .openDiagnosis(),
                  icon: const Icon(Icons.forum_outlined),
                  label: const Text('Diagnosi'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _ProblemsError extends StatelessWidget {
  const _ProblemsError({required this.onRetry});

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
            const Expanded(child: Text('Problemi non caricati.')),
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

String _statusLabel(String status) {
  return switch (status) {
    'open' => 'Aperto',
    'in_diagnosis' => 'In diagnosi',
    'waiting_professional' => 'In attesa',
    'scheduled' => 'Programmato',
    'resolved' => 'Risolto',
    'closed' => 'Chiuso',
    'cancelled' => 'Annullato',
    _ => status,
  };
}

String _priorityLabel(String priority) {
  return switch (priority) {
    'low' => 'Priorità bassa',
    'normal' => 'Priorità normale',
    'high' => 'Priorità alta',
    'urgent' => 'Urgente',
    _ => 'Priorità non definita',
  };
}

String _feedbackMessage(DiagnosticFeedbackResult result) {
  if (result.resolved) {
    return 'Caso segnato come risolto.';
  }
  return result.nextActions.isEmpty
      ? 'Diagnostica aggiornata.'
      : result.nextActions.first;
}

String _messageStatus(String status) {
  return switch (status) {
    'queued' => 'Risposta in coda.',
    'processing' => 'Risposta in elaborazione.',
    'failed' => 'Risposta non disponibile.',
    _ => '',
  };
}

String _shareStatusLabel(String status) {
  return switch (status) {
    'pending' => 'in attesa',
    'accepted' => 'accettata',
    'rejected' => 'rifiutata',
    'revoked' => 'revocata',
    _ => status,
  };
}
