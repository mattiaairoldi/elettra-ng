import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/problem_models.dart';
import '../data/problems_repository.dart';

class ProblemsScreen extends ConsumerWidget {
  const ProblemsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final problems = ref.watch(problemsProvider);

    return problems.when(
      data: (items) {
        if (items.isEmpty) {
          return const _EmptyProblems();
        }

        return RefreshIndicator(
          onRefresh: () async => ref.invalidate(problemsProvider),
          child: ListView.separated(
            padding: EdgeInsets.zero,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemBuilder: (context, index) =>
                _ProblemCard(problem: items[index]),
            separatorBuilder: (context, index) => const SizedBox(height: 8),
            itemCount: items.length,
          ),
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
}

class _ProblemCard extends StatelessWidget {
  const _ProblemCard({required this.problem});

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
                Text(_priorityLabel(problem.priority)),
              ],
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

class _EmptyProblems extends StatelessWidget {
  const _EmptyProblems();

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            const Icon(Icons.check_circle_outline),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                'Non ci sono problemi aperti.',
                style: Theme.of(context).textTheme.bodyLarge,
              ),
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
