import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../problems/data/problem_models.dart';
import '../../problems/data/problems_repository.dart';
import '../../shell/data/shell_navigation.dart';

const _allCategoriesValue = -1;

class ProfessionalsScreen extends ConsumerStatefulWidget {
  const ProfessionalsScreen({super.key});

  @override
  ConsumerState<ProfessionalsScreen> createState() =>
      _ProfessionalsScreenState();
}

class _ProfessionalsScreenState extends ConsumerState<ProfessionalsScreen> {
  int? _selectedCategoryId;

  @override
  Widget build(BuildContext context) {
    final categories = ref.watch(categoriesProvider);
    final categoryItems = categories.when(
      data: (items) => items,
      error: (_, _) => const <ProblemCategory>[],
      loading: () => const <ProblemCategory>[],
    );
    final categoryNamesById = {
      for (final category in categoryItems) category.id: category.name,
    };
    final professionals = ref.watch(professionalsProvider(_selectedCategoryId));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _FilterPanel(
          selectedCategoryId: _selectedCategoryId,
          categories: categories,
          onChanged: (categoryId) {
            setState(() => _selectedCategoryId = categoryId);
          },
          onRefresh: _refresh,
        ),
        const SizedBox(height: 16),
        professionals.when(
          data: (items) => _ProfessionalsList(
            professionals: items,
            selectedCategoryId: _selectedCategoryId,
            categoryNamesById: categoryNamesById,
            onResetCategory: _selectedCategoryId == null
                ? null
                : () => setState(() => _selectedCategoryId = null),
            onOpenProblems: () =>
                ref.read(shellNavigationProvider.notifier).openProblems(),
            onOpenDiagnosis: () =>
                ref.read(shellNavigationProvider.notifier).openDiagnosis(),
          ),
          loading: () => const _LoadingPanel(),
          error: (error, _) => _ErrorPanel(onRetry: _refresh),
        ),
      ],
    );
  }

  void _refresh() {
    ref.invalidate(categoriesProvider);
    ref.invalidate(professionalsProvider(_selectedCategoryId));
  }
}

class _FilterPanel extends StatelessWidget {
  const _FilterPanel({
    required this.selectedCategoryId,
    required this.categories,
    required this.onChanged,
    required this.onRefresh,
  });

  final int? selectedCategoryId;
  final AsyncValue<List<ProblemCategory>> categories;
  final ValueChanged<int?> onChanged;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.tune_outlined),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Filtro tecnici',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                IconButton(
                  tooltip: 'Aggiorna tecnici',
                  onPressed: onRefresh,
                  icon: const Icon(Icons.refresh),
                ),
              ],
            ),
            const SizedBox(height: 12),
            categories.when(
              data: (items) {
                final selectedValue =
                    items.any((category) => category.id == selectedCategoryId)
                    ? selectedCategoryId!
                    : _allCategoriesValue;
                return DropdownButtonFormField<int>(
                  initialValue: selectedValue,
                  isExpanded: true,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    labelText: 'Categoria',
                    prefixIcon: Icon(Icons.category_outlined),
                  ),
                  items: [
                    const DropdownMenuItem(
                      value: _allCategoriesValue,
                      child: Text('Tutte le categorie'),
                    ),
                    for (final category in items)
                      DropdownMenuItem(
                        value: category.id,
                        child: Text(category.name),
                      ),
                  ],
                  onChanged: (value) => onChanged(
                    value == null || value == _allCategoriesValue
                        ? null
                        : value,
                  ),
                );
              },
              loading: () => const LinearProgressIndicator(),
              error: (error, _) => _InlineError(
                label: 'Categorie non disponibili.',
                onRetry: onRefresh,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ProfessionalsList extends StatelessWidget {
  const _ProfessionalsList({
    required this.professionals,
    required this.selectedCategoryId,
    required this.categoryNamesById,
    required this.onResetCategory,
    required this.onOpenProblems,
    required this.onOpenDiagnosis,
  });

  final List<ProfessionalProfileSummary> professionals;
  final int? selectedCategoryId;
  final Map<int, String> categoryNamesById;
  final VoidCallback? onResetCategory;
  final VoidCallback onOpenProblems;
  final VoidCallback onOpenDiagnosis;

  @override
  Widget build(BuildContext context) {
    if (professionals.isEmpty) {
      return _EmptyProfessionalsPanel(
        filtered: selectedCategoryId != null,
        onResetCategory: onResetCategory,
        onOpenDiagnosis: onOpenDiagnosis,
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                'Tecnici disponibili',
                style: Theme.of(
                  context,
                ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
              ),
            ),
            _CountPill(count: professionals.length),
          ],
        ),
        const SizedBox(height: 10),
        for (final professional in professionals) ...[
          _ProfessionalCard(
            professional: professional,
            categoryNamesById: categoryNamesById,
            onOpenProblems: onOpenProblems,
          ),
          const SizedBox(height: 10),
        ],
      ],
    );
  }
}

class _ProfessionalCard extends StatelessWidget {
  const _ProfessionalCard({
    required this.professional,
    required this.categoryNamesById,
    required this.onOpenProblems,
  });

  final ProfessionalProfileSummary professional;
  final Map<int, String> categoryNamesById;
  final VoidCallback onOpenProblems;

  @override
  Widget build(BuildContext context) {
    final categoryNames = professional.categoryIds
        .map((id) => categoryNamesById[id])
        .whereType<String>()
        .where((name) => name.trim().isNotEmpty)
        .toList();

    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(
                  radius: 20,
                  child: Text(_initialsFor(professional.displayName)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        professional.displayName,
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w700),
                      ),
                      if (professional.serviceAreaText.isNotEmpty)
                        _MetaLine(
                          icon: Icons.place_outlined,
                          label: professional.serviceAreaText,
                        ),
                    ],
                  ),
                ),
              ],
            ),
            if (professional.bio.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                professional.bio,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
            ],
            if (categoryNames.isNotEmpty) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final name in categoryNames) _CategoryChip(label: name),
                ],
              ),
            ],
            if (professional.phone.isNotEmpty ||
                professional.emailPublic.isNotEmpty) ...[
              const SizedBox(height: 12),
              if (professional.phone.isNotEmpty)
                _MetaLine(icon: Icons.call_outlined, label: professional.phone),
              if (professional.emailPublic.isNotEmpty)
                _MetaLine(
                  icon: Icons.mail_outline,
                  label: professional.emailPublic,
                ),
            ],
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: onOpenProblems,
                icon: const Icon(Icons.assignment_outlined),
                label: const Text('Vai ai problemi'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MetaLine extends StatelessWidget {
  const _MetaLine({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18),
          const SizedBox(width: 6),
          Expanded(child: Text(label)),
        ],
      ),
    );
  }
}

class _CategoryChip extends StatelessWidget {
  const _CategoryChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: scheme.secondaryContainer,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Text(
          label,
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
            color: scheme.onSecondaryContainer,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}

class _CountPill extends StatelessWidget {
  const _CountPill({required this.count});

  final int count;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        border: Border.all(color: scheme.outlineVariant),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Text('$count'),
      ),
    );
  }
}

class _EmptyProfessionalsPanel extends StatelessWidget {
  const _EmptyProfessionalsPanel({
    required this.filtered,
    required this.onResetCategory,
    required this.onOpenDiagnosis,
  });

  final bool filtered;
  final VoidCallback? onResetCategory;
  final VoidCallback onOpenDiagnosis;

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _PanelTitle(
              icon: Icons.engineering_outlined,
              label: 'Nessun tecnico disponibile',
            ),
            const SizedBox(height: 8),
            Text(
              filtered
                  ? 'Nessun tecnico disponibile per questa categoria.'
                  : 'Nessun tecnico disponibile al momento.',
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                if (filtered)
                  OutlinedButton.icon(
                    onPressed: onResetCategory,
                    icon: const Icon(Icons.filter_alt_off_outlined),
                    label: const Text('Rimuovi filtro'),
                  ),
                FilledButton.tonalIcon(
                  onPressed: onOpenDiagnosis,
                  icon: const Icon(Icons.forum_outlined),
                  label: const Text('Avvia diagnosi'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _LoadingPanel extends StatelessWidget {
  const _LoadingPanel();

  @override
  Widget build(BuildContext context) {
    return const Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Row(
          children: [
            SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            SizedBox(width: 12),
            Text('Caricamento tecnici'),
          ],
        ),
      ),
    );
  }
}

class _ErrorPanel extends StatelessWidget {
  const _ErrorPanel({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _PanelTitle(
              icon: Icons.error_outline,
              label: 'Tecnici non disponibili',
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Riprova'),
            ),
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
    return Row(
      children: [
        Expanded(child: Text(label)),
        TextButton.icon(
          onPressed: onRetry,
          icon: const Icon(Icons.refresh),
          label: const Text('Riprova'),
        ),
      ],
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
        const SizedBox(width: 10),
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

String _initialsFor(String name) {
  final parts = name
      .trim()
      .split(RegExp(r'\s+'))
      .where((part) => part.isNotEmpty)
      .toList();
  if (parts.isEmpty) {
    return '?';
  }
  final initials = parts.take(2).map((part) => part[0]).join();
  return initials.toUpperCase();
}
