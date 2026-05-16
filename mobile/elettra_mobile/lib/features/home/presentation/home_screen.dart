import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../problems/data/problems_repository.dart';
import '../../shell/data/shell_navigation.dart';
import '../data/home_models.dart';
import '../data/home_repository.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final overview = ref.watch(homeOverviewProvider);

    return overview.when(
      data: (data) {
        if (data.properties.isEmpty) {
          return _EmptyHome(
            onAddProperty: () => _showCreatePropertyDialog(context, ref),
          );
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            for (final property in data.properties) ...[
              _PropertyHeader(
                property: property,
                onAddAsset: () => _showCreateAssetDialog(
                  context,
                  ref,
                  property,
                  data.categories,
                ),
              ),
              const SizedBox(height: 8),
              ..._assetsFor(data, property).map(
                (asset) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: _AssetCard(
                    asset: asset,
                    events: data.eventsByAssetId[asset.id] ?? const [],
                    reminders: data.remindersByAssetId[asset.id] ?? const [],
                    attachments:
                        data.attachmentsByAssetId[asset.id] ?? const [],
                    onAddEvent: () =>
                        _showCreateEventDialog(context, ref, asset),
                    onAddReminder: () =>
                        _showCreateReminderDialog(context, ref, asset),
                    onUploadAttachment: () =>
                        _pickAndUploadAttachment(context, ref, asset),
                    onCreateProblem: () =>
                        _showCreateProblemDialog(context, ref, asset),
                    onCompleteReminder: (reminder) =>
                        _completeReminder(context, ref, reminder),
                  ),
                ),
              ),
              if (_assetsFor(data, property).isEmpty)
                _EmptyPropertyAssets(
                  onAddAsset: () => _showCreateAssetDialog(
                    context,
                    ref,
                    property,
                    data.categories,
                  ),
                ),
              const SizedBox(height: 12),
            ],
          ],
        );
      },
      error: (error, stackTrace) =>
          _HomeError(onRetry: () => ref.invalidate(homeOverviewProvider)),
      loading: () => const Padding(
        padding: EdgeInsets.symmetric(vertical: 32),
        child: Center(child: CircularProgressIndicator()),
      ),
    );
  }

  List<HomeAsset> _assetsFor(HomeOverview overview, HomeProperty property) {
    return overview.assets
        .where((asset) => asset.propertyId == property.id)
        .toList();
  }

  Future<void> _showCreatePropertyDialog(
    BuildContext context,
    WidgetRef ref,
  ) async {
    var created = false;
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => _CreatePropertyDialog(
        onSubmit: (payload) async {
          await ref
              .read(homeRepositoryProvider)
              .createProperty(
                name: payload.name,
                addressText: payload.addressText,
                city: payload.city,
                notes: payload.notes,
              );
          created = true;
          ref.invalidate(homeOverviewProvider);
        },
      ),
    );
    if (created && context.mounted) {
      _showSnackBar(context, 'Casa aggiunta.');
    }
  }

  Future<void> _showCreateAssetDialog(
    BuildContext context,
    WidgetRef ref,
    HomeProperty property,
    List<HomeCategory> categories,
  ) async {
    if (categories.isEmpty) {
      _showSnackBar(context, 'Categorie non disponibili.');
      return;
    }
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => _CreateAssetDialog(
        property: property,
        categories: categories,
        onSubmit: (payload) async {
          await ref
              .read(homeRepositoryProvider)
              .createAsset(
                propertyId: property.id,
                categoryId: payload.categoryId,
                name: payload.name,
                description: payload.description,
                locationText: payload.locationText,
                metadata: payload.metadata,
              );
          ref.invalidate(homeOverviewProvider);
        },
      ),
    );
  }

  Future<void> _showCreateEventDialog(
    BuildContext context,
    WidgetRef ref,
    HomeAsset asset,
  ) async {
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => _CreateEventDialog(
        asset: asset,
        onSubmit: (payload) async {
          await ref
              .read(homeRepositoryProvider)
              .createMaintenanceEvent(
                assetId: asset.id,
                eventType: payload.eventType,
                title: payload.title,
                description: payload.description,
                eventDate: payload.eventDate,
              );
          ref.invalidate(homeOverviewProvider);
        },
      ),
    );
  }

  Future<void> _showCreateReminderDialog(
    BuildContext context,
    WidgetRef ref,
    HomeAsset asset,
  ) async {
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => _CreateReminderDialog(
        asset: asset,
        onSubmit: (payload) async {
          await ref
              .read(homeRepositoryProvider)
              .createMaintenanceReminder(
                assetId: asset.id,
                title: payload.title,
                description: payload.description,
                dueAt: payload.dueAt,
                recurrenceRule: payload.recurrenceRule,
              );
          ref.invalidate(homeOverviewProvider);
        },
      ),
    );
  }

  Future<void> _completeReminder(
    BuildContext context,
    WidgetRef ref,
    HomeMaintenanceReminder reminder,
  ) async {
    await ref.read(homeRepositoryProvider).completeReminder(reminder.id);
    ref.invalidate(homeOverviewProvider);
    if (context.mounted) {
      _showSnackBar(context, 'Promemoria completato.');
    }
  }

  Future<void> _pickAndUploadAttachment(
    BuildContext context,
    WidgetRef ref,
    HomeAsset asset,
  ) async {
    try {
      final result = await FilePicker.pickFiles(withData: true);
      if (result == null || result.files.isEmpty) {
        return;
      }
      final file = result.files.single;
      final bytes = file.bytes;
      if (bytes == null) {
        if (context.mounted) {
          _showSnackBar(context, 'File non leggibile.');
        }
        return;
      }

      await ref
          .read(homeRepositoryProvider)
          .uploadAssetAttachment(
            assetId: asset.id,
            fileName: file.name,
            bytes: bytes,
            attachmentType: _attachmentTypeForFileName(file.name),
          );
      ref.invalidate(homeOverviewProvider);
      if (context.mounted) {
        _showSnackBar(context, 'Allegato caricato.');
      }
    } catch (_) {
      if (context.mounted) {
        _showSnackBar(context, 'Caricamento non riuscito.');
      }
    }
  }

  Future<void> _showCreateProblemDialog(
    BuildContext context,
    WidgetRef ref,
    HomeAsset asset,
  ) async {
    var created = false;
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => _CreateProblemDialog(
        asset: asset,
        onSubmit: (payload) async {
          await ref
              .read(homeRepositoryProvider)
              .createProblemFromAsset(
                assetId: asset.id,
                categoryId: asset.categoryId,
                title: payload.title,
                description: payload.description,
                priority: payload.priority,
              );
          created = true;
          ref.invalidate(problemsProvider);
        },
      ),
    );
    if (created && context.mounted) {
      _showSnackBar(context, 'Problematica aperta.');
    }
  }

  void _showSnackBar(BuildContext context, String message) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }
}

class _PropertyHeader extends StatelessWidget {
  const _PropertyHeader({required this.property, required this.onAddAsset});

  final HomeProperty property;
  final VoidCallback onAddAsset;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final subtitle = [
      if (property.addressText.isNotEmpty) property.addressText,
      if (property.city.isNotEmpty) property.city,
    ].join(' · ');

    return Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.home_work_outlined, color: scheme.primary),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  property.name,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                if (subtitle.isNotEmpty)
                  Text(
                    subtitle,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: scheme.onSurfaceVariant,
                    ),
                  ),
              ],
            ),
          ),
          IconButton(
            tooltip: 'Aggiungi asset',
            onPressed: onAddAsset,
            icon: const Icon(Icons.add),
          ),
        ],
      ),
    );
  }
}

class _AssetCard extends StatelessWidget {
  const _AssetCard({
    required this.asset,
    required this.events,
    required this.reminders,
    required this.attachments,
    required this.onAddEvent,
    required this.onAddReminder,
    required this.onUploadAttachment,
    required this.onCreateProblem,
    required this.onCompleteReminder,
  });

  final HomeAsset asset;
  final List<HomeMaintenanceEvent> events;
  final List<HomeMaintenanceReminder> reminders;
  final List<HomeAttachment> attachments;
  final VoidCallback onAddEvent;
  final VoidCallback onAddReminder;
  final VoidCallback onUploadAttachment;
  final VoidCallback onCreateProblem;
  final ValueChanged<HomeMaintenanceReminder> onCompleteReminder;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final manufacturer = asset.metadataValue('manufacturer');
    final model = asset.metadataValue('model');
    final serialNumber = asset.metadataValue('serial_number');

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.inventory_2_outlined, color: scheme.primary),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        asset.name,
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w700),
                      ),
                      if (asset.locationText.isNotEmpty)
                        Text(
                          asset.locationText,
                          style: Theme.of(context).textTheme.bodySmall
                              ?.copyWith(color: scheme.onSurfaceVariant),
                        ),
                    ],
                  ),
                ),
              ],
            ),
            if (asset.description.isNotEmpty) ...[
              const SizedBox(height: 10),
              Text(asset.description),
            ],
            if (manufacturer != null ||
                model != null ||
                serialNumber != null) ...[
              const SizedBox(height: 12),
              _MetadataRows(
                rows: [
                  if (manufacturer != null) ('Marca', manufacturer),
                  if (model != null) ('Modello', model),
                  if (serialNumber != null) ('Seriale', serialNumber),
                ],
              ),
            ],
            const SizedBox(height: 14),
            _AssetTimeline(
              events: events,
              reminders: reminders,
              onCompleteReminder: onCompleteReminder,
            ),
            const SizedBox(height: 12),
            _AssetDocuments(attachments: attachments),
            const SizedBox(height: 14),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                OutlinedButton.icon(
                  onPressed: onAddEvent,
                  icon: const Icon(Icons.history_outlined),
                  label: const Text('Attività'),
                ),
                OutlinedButton.icon(
                  onPressed: onAddReminder,
                  icon: const Icon(Icons.event_available_outlined),
                  label: const Text('Promemoria'),
                ),
                OutlinedButton.icon(
                  onPressed: onUploadAttachment,
                  icon: const Icon(Icons.attach_file),
                  label: const Text('Allegato'),
                ),
                FilledButton.icon(
                  onPressed: onCreateProblem,
                  icon: const Icon(Icons.report_problem_outlined),
                  label: const Text('Problema'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _MetadataRows extends StatelessWidget {
  const _MetadataRows({required this.rows});

  final List<(String, String)> rows;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Column(
      children: [
        for (final row in rows)
          Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Row(
              children: [
                SizedBox(
                  width: 72,
                  child: Text(
                    row.$1,
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: scheme.onSurfaceVariant,
                    ),
                  ),
                ),
                Expanded(
                  child: Text(
                    row.$2,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}

class _AssetTimeline extends StatelessWidget {
  const _AssetTimeline({
    required this.events,
    required this.reminders,
    required this.onCompleteReminder,
  });

  final List<HomeMaintenanceEvent> events;
  final List<HomeMaintenanceReminder> reminders;
  final ValueChanged<HomeMaintenanceReminder> onCompleteReminder;

  @override
  Widget build(BuildContext context) {
    final latestEvent = events.isEmpty ? null : events.first;
    final nextReminder = _firstActiveReminder(reminders);

    return Column(
      children: [
        _TimelineRow(
          icon: Icons.history_outlined,
          label: 'Ultima attività',
          value: latestEvent == null
              ? 'Nessuna attività registrata'
              : latestEvent.title,
          detail: latestEvent == null
              ? null
              : _formatDate(latestEvent.eventDate),
        ),
        const SizedBox(height: 8),
        _TimelineRow(
          icon: Icons.event_available_outlined,
          label: 'Prossima scadenza',
          value: nextReminder == null
              ? 'Nessun promemoria attivo'
              : nextReminder.title,
          detail: nextReminder == null ? null : _formatDate(nextReminder.dueAt),
          trailing: nextReminder == null
              ? null
              : IconButton(
                  tooltip: 'Completa',
                  onPressed: () => onCompleteReminder(nextReminder),
                  icon: const Icon(Icons.check),
                ),
        ),
      ],
    );
  }

  HomeMaintenanceReminder? _firstActiveReminder(
    List<HomeMaintenanceReminder> reminders,
  ) {
    for (final reminder in reminders) {
      if (reminder.status == 'active') {
        return reminder;
      }
    }
    return null;
  }
}

class _AssetDocuments extends StatelessWidget {
  const _AssetDocuments({required this.attachments});

  final List<HomeAttachment> attachments;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final visibleAttachments = attachments.take(3).toList();

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(Icons.folder_outlined, size: 20, color: scheme.onSurfaceVariant),
        const SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Documenti',
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
              ),
              if (attachments.isEmpty)
                const Text('Nessun allegato')
              else
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    for (final attachment in visibleAttachments)
                      Chip(
                        avatar: Icon(_iconForAttachment(attachment), size: 18),
                        label: ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 180),
                          child: Text(
                            attachment.fileName,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        visualDensity: VisualDensity.compact,
                      ),
                    if (attachments.length > visibleAttachments.length)
                      Chip(
                        label: Text(
                          '+${attachments.length - visibleAttachments.length}',
                        ),
                        visualDensity: VisualDensity.compact,
                      ),
                  ],
                ),
            ],
          ),
        ),
      ],
    );
  }

  IconData _iconForAttachment(HomeAttachment attachment) {
    return switch (attachment.attachmentType) {
      'image' => Icons.image_outlined,
      'document' => Icons.description_outlined,
      _ => Icons.insert_drive_file_outlined,
    };
  }
}

class _TimelineRow extends StatelessWidget {
  const _TimelineRow({
    required this.icon,
    required this.label,
    required this.value,
    this.detail,
    this.trailing,
  });

  final IconData icon;
  final String label;
  final String value;
  final String? detail;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 20, color: scheme.onSurfaceVariant),
        const SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
              ),
              Text(value),
            ],
          ),
        ),
        if (detail != null) ...[
          const SizedBox(width: 8),
          Text(
            detail!,
            style: Theme.of(
              context,
            ).textTheme.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
          ),
        ],
        if (trailing != null) ...[const SizedBox(width: 4), trailing!],
      ],
    );
  }
}

class _CreatePropertyDialog extends StatefulWidget {
  const _CreatePropertyDialog({required this.onSubmit});

  final Future<void> Function(_PropertyFormPayload payload) onSubmit;

  @override
  State<_CreatePropertyDialog> createState() => _CreatePropertyDialogState();
}

class _CreatePropertyDialogState extends State<_CreatePropertyDialog> {
  final _nameController = TextEditingController();
  final _addressController = TextEditingController();
  final _cityController = TextEditingController();
  final _notesController = TextEditingController();
  var _submitting = false;
  String? _error;

  @override
  void dispose() {
    _nameController.dispose();
    _addressController.dispose();
    _cityController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Aggiungi casa'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _nameController,
              enabled: !_submitting,
              decoration: const InputDecoration(labelText: 'Nome'),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _addressController,
              enabled: !_submitting,
              decoration: const InputDecoration(labelText: 'Indirizzo'),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _cityController,
              enabled: !_submitting,
              decoration: const InputDecoration(labelText: 'Città'),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _notesController,
              enabled: !_submitting,
              decoration: const InputDecoration(labelText: 'Note'),
              minLines: 2,
              maxLines: 4,
            ),
            if (_error != null) _DialogError(message: _error!),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _submitting ? null : () => Navigator.of(context).pop(),
          child: const Text('Annulla'),
        ),
        FilledButton(
          onPressed: _submitting ? null : _submit,
          child: _submitting
              ? const SizedBox.square(
                  dimension: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Salva'),
        ),
      ],
    );
  }

  Future<void> _submit() async {
    final name = _nameController.text.trim();
    final address = _addressController.text.trim();
    final city = _cityController.text.trim();
    final notes = _notesController.text.trim();
    if (name.isEmpty) {
      setState(() => _error = 'Inserisci un nome per la casa.');
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      await widget.onSubmit(
        _PropertyFormPayload(
          name: name,
          addressText: address,
          city: city,
          notes: notes,
        ),
      );
      if (mounted) {
        Navigator.of(context).pop();
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _submitting = false;
          _error = 'Creazione casa non riuscita.';
        });
      }
    }
  }
}

class _PropertyFormPayload {
  const _PropertyFormPayload({
    required this.name,
    required this.addressText,
    required this.city,
    required this.notes,
  });

  final String name;
  final String addressText;
  final String city;
  final String notes;
}

class _CreateAssetDialog extends StatefulWidget {
  const _CreateAssetDialog({
    required this.property,
    required this.categories,
    required this.onSubmit,
  });

  final HomeProperty property;
  final List<HomeCategory> categories;
  final Future<void> Function(_AssetFormPayload payload) onSubmit;

  @override
  State<_CreateAssetDialog> createState() => _CreateAssetDialogState();
}

class _CreateAssetDialogState extends State<_CreateAssetDialog> {
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _locationController = TextEditingController();
  final _manufacturerController = TextEditingController();
  final _modelController = TextEditingController();
  final _serialController = TextEditingController();
  late int _categoryId;
  var _submitting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _categoryId = widget.categories.first.id;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    _locationController.dispose();
    _manufacturerController.dispose();
    _modelController.dispose();
    _serialController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Nuovo asset'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                widget.property.name,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<int>(
              initialValue: _categoryId,
              decoration: const InputDecoration(labelText: 'Categoria'),
              items: [
                for (final category in widget.categories)
                  DropdownMenuItem(
                    value: category.id,
                    child: Text(category.name),
                  ),
              ],
              onChanged: _submitting
                  ? null
                  : (value) =>
                        setState(() => _categoryId = value ?? _categoryId),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _nameController,
              enabled: !_submitting,
              decoration: const InputDecoration(labelText: 'Nome'),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _locationController,
              enabled: !_submitting,
              decoration: const InputDecoration(labelText: 'Posizione'),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _manufacturerController,
              enabled: !_submitting,
              decoration: const InputDecoration(labelText: 'Marca'),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _modelController,
              enabled: !_submitting,
              decoration: const InputDecoration(labelText: 'Modello'),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _serialController,
              enabled: !_submitting,
              decoration: const InputDecoration(labelText: 'Seriale'),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _descriptionController,
              enabled: !_submitting,
              decoration: const InputDecoration(labelText: 'Note'),
              minLines: 2,
              maxLines: 4,
            ),
            if (_error != null) _DialogError(message: _error!),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _submitting ? null : () => Navigator.of(context).pop(),
          child: const Text('Annulla'),
        ),
        FilledButton(
          onPressed: _submitting ? null : _submit,
          child: _submitting
              ? const SizedBox.square(
                  dimension: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Salva'),
        ),
      ],
    );
  }

  Future<void> _submit() async {
    final name = _nameController.text.trim();
    if (name.isEmpty) {
      setState(() => _error = 'Nome richiesto.');
      return;
    }

    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      await widget.onSubmit(
        _AssetFormPayload(
          categoryId: _categoryId,
          name: name,
          description: _descriptionController.text.trim(),
          locationText: _locationController.text.trim(),
          metadata: {
            if (_manufacturerController.text.trim().isNotEmpty)
              'manufacturer': _manufacturerController.text.trim(),
            if (_modelController.text.trim().isNotEmpty)
              'model': _modelController.text.trim(),
            if (_serialController.text.trim().isNotEmpty)
              'serial_number': _serialController.text.trim(),
          },
        ),
      );
      if (mounted) {
        Navigator.of(context).pop();
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _submitting = false;
          _error = 'Salvataggio non riuscito.';
        });
      }
    }
  }
}

class _CreateEventDialog extends StatefulWidget {
  const _CreateEventDialog({required this.asset, required this.onSubmit});

  final HomeAsset asset;
  final Future<void> Function(_EventFormPayload payload) onSubmit;

  @override
  State<_CreateEventDialog> createState() => _CreateEventDialogState();
}

class _CreateEventDialogState extends State<_CreateEventDialog> {
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  var _eventType = 'cleaning';
  var _eventDate = DateTime.now();
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
    return AlertDialog(
      title: const Text('Nuova attività'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                widget.asset.name,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _eventType,
              decoration: const InputDecoration(labelText: 'Tipo'),
              items: const [
                DropdownMenuItem(value: 'cleaning', child: Text('Pulizia')),
                DropdownMenuItem(
                  value: 'replacement',
                  child: Text('Sostituzione'),
                ),
                DropdownMenuItem(value: 'inspection', child: Text('Controllo')),
                DropdownMenuItem(value: 'repair', child: Text('Riparazione')),
                DropdownMenuItem(value: 'note', child: Text('Nota')),
                DropdownMenuItem(value: 'other', child: Text('Altro')),
              ],
              onChanged: _submitting
                  ? null
                  : (value) => setState(() => _eventType = value ?? _eventType),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _titleController,
              enabled: !_submitting,
              decoration: const InputDecoration(labelText: 'Titolo'),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _descriptionController,
              enabled: !_submitting,
              decoration: const InputDecoration(labelText: 'Note'),
              minLines: 2,
              maxLines: 4,
            ),
            const SizedBox(height: 12),
            _DateField(
              label: 'Data',
              value: _eventDate,
              onPick: _submitting
                  ? null
                  : () async => _pickDate((value) => _eventDate = value),
            ),
            if (_error != null) _DialogError(message: _error!),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _submitting ? null : () => Navigator.of(context).pop(),
          child: const Text('Annulla'),
        ),
        FilledButton(
          onPressed: _submitting ? null : _submit,
          child: _submitting
              ? const SizedBox.square(
                  dimension: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Salva'),
        ),
      ],
    );
  }

  Future<void> _pickDate(ValueChanged<DateTime> update) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _eventDate,
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
    );
    if (picked != null && mounted) {
      setState(() => update(picked));
    }
  }

  Future<void> _submit() async {
    final title = _titleController.text.trim();
    if (title.isEmpty) {
      setState(() => _error = 'Titolo richiesto.');
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      await widget.onSubmit(
        _EventFormPayload(
          eventType: _eventType,
          title: title,
          description: _descriptionController.text.trim(),
          eventDate: _eventDate,
        ),
      );
      if (mounted) {
        Navigator.of(context).pop();
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _submitting = false;
          _error = 'Salvataggio non riuscito.';
        });
      }
    }
  }
}

class _CreateReminderDialog extends StatefulWidget {
  const _CreateReminderDialog({required this.asset, required this.onSubmit});

  final HomeAsset asset;
  final Future<void> Function(_ReminderFormPayload payload) onSubmit;

  @override
  State<_CreateReminderDialog> createState() => _CreateReminderDialogState();
}

class _CreateReminderDialogState extends State<_CreateReminderDialog> {
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  var _dueAt = DateTime.now().add(const Duration(days: 90));
  var _recurrenceRule = 'none';
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
    return AlertDialog(
      title: const Text('Nuovo promemoria'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                widget.asset.name,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _titleController,
              enabled: !_submitting,
              decoration: const InputDecoration(labelText: 'Titolo'),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _descriptionController,
              enabled: !_submitting,
              decoration: const InputDecoration(labelText: 'Note'),
              minLines: 2,
              maxLines: 4,
            ),
            const SizedBox(height: 12),
            _DateField(
              label: 'Scadenza',
              value: _dueAt,
              onPick: _submitting ? null : _pickDate,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _recurrenceRule,
              decoration: const InputDecoration(labelText: 'Ricorrenza'),
              items: const [
                DropdownMenuItem(value: 'none', child: Text('Nessuna')),
                DropdownMenuItem(value: 'monthly', child: Text('Mensile')),
                DropdownMenuItem(
                  value: 'quarterly',
                  child: Text('Trimestrale'),
                ),
                DropdownMenuItem(
                  value: 'semiannual',
                  child: Text('Semestrale'),
                ),
                DropdownMenuItem(value: 'annual', child: Text('Annuale')),
              ],
              onChanged: _submitting
                  ? null
                  : (value) => setState(
                      () => _recurrenceRule = value ?? _recurrenceRule,
                    ),
            ),
            if (_error != null) _DialogError(message: _error!),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _submitting ? null : () => Navigator.of(context).pop(),
          child: const Text('Annulla'),
        ),
        FilledButton(
          onPressed: _submitting ? null : _submit,
          child: _submitting
              ? const SizedBox.square(
                  dimension: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Salva'),
        ),
      ],
    );
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _dueAt,
      firstDate: DateTime.now(),
      lastDate: DateTime(2100),
    );
    if (picked != null && mounted) {
      setState(() => _dueAt = picked);
    }
  }

  Future<void> _submit() async {
    final title = _titleController.text.trim();
    if (title.isEmpty) {
      setState(() => _error = 'Titolo richiesto.');
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      await widget.onSubmit(
        _ReminderFormPayload(
          title: title,
          description: _descriptionController.text.trim(),
          dueAt: _dueAt,
          recurrenceRule: _recurrenceRule,
        ),
      );
      if (mounted) {
        Navigator.of(context).pop();
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _submitting = false;
          _error = 'Salvataggio non riuscito.';
        });
      }
    }
  }
}

class _CreateProblemDialog extends StatefulWidget {
  const _CreateProblemDialog({required this.asset, required this.onSubmit});

  final HomeAsset asset;
  final Future<void> Function(_ProblemFormPayload payload) onSubmit;

  @override
  State<_CreateProblemDialog> createState() => _CreateProblemDialogState();
}

class _CreateProblemDialogState extends State<_CreateProblemDialog> {
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  var _priority = 'normal';
  var _submitting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _titleController.text = 'Problema su ${widget.asset.name}';
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Nuova problematica'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                widget.asset.name,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _titleController,
              enabled: !_submitting,
              decoration: const InputDecoration(labelText: 'Titolo'),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _descriptionController,
              enabled: !_submitting,
              decoration: const InputDecoration(labelText: 'Descrizione'),
              minLines: 3,
              maxLines: 5,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _priority,
              decoration: const InputDecoration(labelText: 'Priorità'),
              items: const [
                DropdownMenuItem(value: 'low', child: Text('Bassa')),
                DropdownMenuItem(value: 'normal', child: Text('Normale')),
                DropdownMenuItem(value: 'high', child: Text('Alta')),
                DropdownMenuItem(value: 'urgent', child: Text('Urgente')),
              ],
              onChanged: _submitting
                  ? null
                  : (value) => setState(() => _priority = value ?? _priority),
            ),
            if (_error != null) _DialogError(message: _error!),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _submitting ? null : () => Navigator.of(context).pop(),
          child: const Text('Annulla'),
        ),
        FilledButton(
          onPressed: _submitting ? null : _submit,
          child: _submitting
              ? const SizedBox.square(
                  dimension: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Apri'),
        ),
      ],
    );
  }

  Future<void> _submit() async {
    final title = _titleController.text.trim();
    if (title.isEmpty) {
      setState(() => _error = 'Titolo richiesto.');
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      await widget.onSubmit(
        _ProblemFormPayload(
          title: title,
          description: _descriptionController.text.trim(),
          priority: _priority,
        ),
      );
      if (mounted) {
        Navigator.of(context).pop();
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _submitting = false;
          _error = 'Apertura non riuscita.';
        });
      }
    }
  }
}

class _DateField extends StatelessWidget {
  const _DateField({
    required this.label,
    required this.value,
    required this.onPick,
  });

  final String label;
  final DateTime value;
  final VoidCallback? onPick;

  @override
  Widget build(BuildContext context) {
    return InputDecorator(
      decoration: InputDecoration(labelText: label),
      child: Row(
        children: [
          Expanded(child: Text(_formatDate(value))),
          IconButton(
            tooltip: 'Scegli data',
            onPressed: onPick,
            icon: const Icon(Icons.calendar_month_outlined),
          ),
        ],
      ),
    );
  }
}

class _DialogError extends StatelessWidget {
  const _DialogError({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Text(
        message,
        style: Theme.of(
          context,
        ).textTheme.bodySmall?.copyWith(color: scheme.error),
      ),
    );
  }
}

class _AssetFormPayload {
  const _AssetFormPayload({
    required this.categoryId,
    required this.name,
    required this.description,
    required this.locationText,
    required this.metadata,
  });

  final int categoryId;
  final String name;
  final String description;
  final String locationText;
  final Map<String, dynamic> metadata;
}

class _EventFormPayload {
  const _EventFormPayload({
    required this.eventType,
    required this.title,
    required this.description,
    required this.eventDate,
  });

  final String eventType;
  final String title;
  final String description;
  final DateTime eventDate;
}

class _ReminderFormPayload {
  const _ReminderFormPayload({
    required this.title,
    required this.description,
    required this.dueAt,
    required this.recurrenceRule,
  });

  final String title;
  final String description;
  final DateTime dueAt;
  final String recurrenceRule;
}

class _ProblemFormPayload {
  const _ProblemFormPayload({
    required this.title,
    required this.description,
    required this.priority,
  });

  final String title;
  final String description;
  final String priority;
}

class _EmptyPropertyAssets extends StatelessWidget {
  const _EmptyPropertyAssets({required this.onAddAsset});

  final VoidCallback onAddAsset;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Nessun asset registrato per questo immobile.',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: onAddAsset,
            icon: const Icon(Icons.add),
            label: const Text('Aggiungi asset'),
          ),
        ],
      ),
    );
  }
}

class _EmptyHome extends ConsumerWidget {
  const _EmptyHome({required this.onAddProperty});

  final VoidCallback onAddProperty;

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
                Icon(Icons.home_work_outlined, color: scheme.primary),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Nessuna casa registrata',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Apri una pratica o continua una diagnosi anche prima di completare la scheda casa.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton.icon(
                  onPressed: () =>
                      ref.read(shellNavigationProvider.notifier).openProblems(),
                  icon: const Icon(Icons.assignment_outlined),
                  label: const Text('Apri problemi'),
                ),
                OutlinedButton.icon(
                  onPressed: () => ref
                      .read(shellNavigationProvider.notifier)
                      .openDiagnosis(),
                  icon: const Icon(Icons.forum_outlined),
                  label: const Text('Continua diagnosi'),
                ),
                OutlinedButton.icon(
                  onPressed: onAddProperty,
                  icon: const Icon(Icons.add_home_outlined),
                  label: const Text('Aggiungi casa'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _HomeError extends StatelessWidget {
  const _HomeError({required this.onRetry});

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
            const Expanded(child: Text('Dati casa non caricati.')),
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

String _formatDate(DateTime? value) {
  if (value == null) {
    return '';
  }
  final day = value.day.toString().padLeft(2, '0');
  final month = value.month.toString().padLeft(2, '0');
  return '$day/$month/${value.year}';
}

String _attachmentTypeForFileName(String fileName) {
  final extension = fileName.split('.').last.toLowerCase();
  if (const {'jpg', 'jpeg', 'png', 'gif', 'webp', 'heic'}.contains(extension)) {
    return 'image';
  }
  if (const {
    'pdf',
    'doc',
    'docx',
    'xls',
    'xlsx',
    'txt',
    'csv',
  }.contains(extension)) {
    return 'document';
  }
  return 'other';
}
