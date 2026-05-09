import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../problems/data/problem_models.dart';
import '../../problems/data/problems_repository.dart';
import '../data/guest_models.dart';
import '../data/guest_repository.dart';

class GuestDiagnosticScreen extends ConsumerStatefulWidget {
  const GuestDiagnosticScreen({super.key, required this.onBackToLogin});

  final VoidCallback onBackToLogin;

  @override
  ConsumerState<GuestDiagnosticScreen> createState() =>
      _GuestDiagnosticScreenState();
}

class _GuestDiagnosticScreenState extends ConsumerState<GuestDiagnosticScreen> {
  final _messageController = TextEditingController();
  int? _selectedChapterId;
  int? _selectedOptionId;
  GuestDiagnosticResult? _result;
  bool _sending = false;
  String? _error;

  @override
  void dispose() {
    _messageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(guestSessionProvider);
    final chapters = ref.watch(diagnosticChaptersProvider(null));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Elettra'),
        leading: IconButton(
          tooltip: 'Accedi',
          onPressed: widget.onBackToLogin,
          icon: const Icon(Icons.arrow_back),
        ),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          children: [
            Text(
              'Diagnosi ospite',
              style: Theme.of(
                context,
              ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            Text(
              'Prova una diagnosi leggera. Per salvare storico, allegati e condivisioni serve accedere.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 16),
            session.when(
              data: (value) =>
                  _QuotaCard(quotas: _result?.quotas ?? value.quotas),
              error: (error, stackTrace) => _InlineError(
                label: 'Sessione ospite non disponibile.',
                onRetry: () => ref.invalidate(guestSessionProvider),
              ),
              loading: () =>
                  const _LoadingCard(label: 'Preparazione sessione ospite'),
            ),
            const SizedBox(height: 12),
            chapters.when(
              data: _buildDiagnosticCard,
              error: (error, stackTrace) => _InlineError(
                label: 'Capitoli diagnostici non caricati.',
                onRetry: () => ref.invalidate(diagnosticChaptersProvider(null)),
              ),
              loading: () =>
                  const _LoadingCard(label: 'Caricamento diagnostica'),
            ),
            if (_result != null) ...[
              const SizedBox(height: 12),
              _GuestResultPanel(
                result: _result!,
                onLogin: widget.onBackToLogin,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildDiagnosticCard(List<DiagnosticChapter> chapters) {
    final chapter = _selectedChapter(chapters);
    final optionId = _selectedOptionIdFor(chapter);
    final scheme = Theme.of(context).colorScheme;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Icon(Icons.manage_search_outlined),
                const SizedBox(width: 8),
                Text(
                  'Percorso rapido',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (chapters.isEmpty)
              const Text('Nessun capitolo diagnostico disponibile.')
            else ...[
              DropdownButtonFormField<int>(
                initialValue: chapter?.id,
                decoration: const InputDecoration(labelText: 'Macro-capitolo'),
                items: [
                  for (final item in chapters)
                    DropdownMenuItem(value: item.id, child: Text(item.name)),
                ],
                onChanged: (value) {
                  setState(() {
                    _selectedChapterId = value;
                    _selectedOptionId = null;
                  });
                },
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
                  onChanged: (value) =>
                      setState(() => _selectedOptionId = value),
                ),
              ],
              const SizedBox(height: 12),
              TextField(
                controller: _messageController,
                enabled: !_sending,
                minLines: 3,
                maxLines: 5,
                decoration: const InputDecoration(
                  labelText: 'Descrivi il problema',
                  prefixIcon: Icon(Icons.edit_note_outlined),
                ),
              ),
              if (_error != null) ...[
                const SizedBox(height: 10),
                Text(_error!, style: TextStyle(color: scheme.error)),
              ],
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: _sending ? null : () => _send(chapter, optionId),
                icon: _sending
                    ? const SizedBox.square(
                        dimension: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.send_outlined),
                label: const Text('Avvia diagnosi'),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: _sending
                    ? null
                    : () => _send(chapter, optionId, useAi: false),
                icon: const Icon(Icons.checklist_outlined),
                label: const Text('Solo consigli salvati'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  DiagnosticChapter? _selectedChapter(List<DiagnosticChapter> chapters) {
    if (chapters.isEmpty) {
      return null;
    }
    for (final chapter in chapters) {
      if (chapter.id == _selectedChapterId) {
        return chapter;
      }
    }
    return chapters.first;
  }

  int? _selectedOptionIdFor(DiagnosticChapter? chapter) {
    if (chapter == null || _selectedOptionId == null) {
      return null;
    }
    return chapter.options.any((option) => option.id == _selectedOptionId)
        ? _selectedOptionId
        : null;
  }

  Future<void> _send(
    DiagnosticChapter? chapter,
    int? optionId, {
    bool useAi = true,
  }) async {
    final message = _messageController.text.trim();
    if (useAi && message.isEmpty) {
      setState(() => _error = 'Descrivi il problema per usare la diagnosi AI.');
      return;
    }

    setState(() {
      _sending = true;
      _error = null;
    });
    try {
      final result = await ref
          .read(guestRepositoryProvider)
          .sendDiagnosticTurn(
            message: message,
            chapterId: chapter?.id,
            optionId: optionId,
            useAi: useAi,
          );
      if (mounted) {
        setState(() {
          _result = result;
          _messageController.clear();
        });
        ref.invalidate(guestSessionProvider);
      }
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Diagnosi ospite non completata.');
      }
    } finally {
      if (mounted) {
        setState(() => _sending = false);
      }
    }
  }
}

class _QuotaCard extends StatelessWidget {
  const _QuotaCard({required this.quotas});

  final GuestQuota quotas;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            Chip(
              avatar: const Icon(Icons.bolt_outlined, size: 18),
              label: Text(
                'AI ${quotas.aiTurnsRemaining}/${quotas.aiTurnLimit}',
              ),
            ),
            Chip(
              avatar: const Icon(Icons.chat_bubble_outline, size: 18),
              label: Text(
                'Messaggi ${quotas.messagesRemaining}/${quotas.messageLimit}',
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _GuestResultPanel extends StatelessWidget {
  const _GuestResultPanel({required this.result, required this.onLogin});

  final GuestDiagnosticResult result;
  final VoidCallback onLogin;

  @override
  Widget build(BuildContext context) {
    final assistant = result.assistantMessage;
    final snapshot = result.snapshot;
    final callToAction = result.callToAction;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (result.adviceSteps.isNotEmpty) ...[
              Text(
                'Consigli guidati',
                style: Theme.of(
                  context,
                ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              for (final step in result.adviceSteps.take(3)) ...[
                _AdviceBox(step: step),
                const SizedBox(height: 8),
              ],
            ],
            if (assistant != null) ...[
              const SizedBox(height: 8),
              _MessageBox(message: assistant),
            ],
            if (snapshot != null) ...[
              const SizedBox(height: 12),
              _SnapshotBox(snapshot: snapshot),
            ],
            if (!callToAction.isEmpty) ...[
              const SizedBox(height: 12),
              _CallToActionBox(callToAction: callToAction, onLogin: onLogin),
            ],
          ],
        ),
      ),
    );
  }
}

class _AdviceBox extends StatelessWidget {
  const _AdviceBox({required this.step});

  final DiagnosticAdviceStep step;

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
          ],
        ),
      ),
    );
  }
}

class _MessageBox extends StatelessWidget {
  const _MessageBox({required this.message});

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
              ? 'Risposta in elaborazione.'
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
          _SnapshotRow(label: 'Rischio', value: snapshot.riskLevel),
        if (snapshot.recommendation.isNotEmpty)
          _SnapshotRow(label: 'Indicazione', value: snapshot.recommendation),
        if (snapshot.nextQuestion.isNotEmpty)
          _SnapshotRow(label: 'Prossima domanda', value: snapshot.nextQuestion),
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

class _CallToActionBox extends StatelessWidget {
  const _CallToActionBox({required this.callToAction, required this.onLogin});

  final GuestCallToAction callToAction;
  final VoidCallback onLogin;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: scheme.primaryContainer,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              callToAction.title,
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                color: scheme.onPrimaryContainer,
                fontWeight: FontWeight.w700,
              ),
            ),
            if (callToAction.message.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                callToAction.message,
                style: TextStyle(color: scheme.onPrimaryContainer),
              ),
            ],
            const SizedBox(height: 10),
            FilledButton.icon(
              onPressed: onLogin,
              icon: const Icon(Icons.login),
              label: Text(callToAction.actionLabel),
            ),
          ],
        ),
      ),
    );
  }
}

class _LoadingCard extends StatelessWidget {
  const _LoadingCard({required this.label});

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
            Expanded(child: Text(label)),
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
