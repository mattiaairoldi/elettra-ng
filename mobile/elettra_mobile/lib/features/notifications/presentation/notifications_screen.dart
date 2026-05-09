import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/notification_models.dart';
import '../data/notification_repository.dart';

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifications = ref.watch(notificationsProvider);
    final summary = ref.watch(notificationSummaryProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _NotificationToolbar(
          unreadCount:
              summary.whenOrNull(data: (data) => data.unreadCount) ?? 0,
        ),
        const SizedBox(height: 12),
        notifications.when(
          data: (items) {
            if (items.isEmpty) {
              return const _EmptyNotifications();
            }
            return Column(
              children: [
                for (final item in items) ...[
                  _NotificationCard(notification: item),
                  const SizedBox(height: 8),
                ],
              ],
            );
          },
          error: (error, stackTrace) => _NotificationsError(
            onRetry: () {
              ref.invalidate(notificationsProvider);
              ref.invalidate(notificationSummaryProvider);
            },
          ),
          loading: () => const _NotificationsLoading(),
        ),
      ],
    );
  }
}

class _NotificationToolbar extends ConsumerWidget {
  const _NotificationToolbar({required this.unreadCount});

  final int unreadCount;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Row(
      children: [
        Expanded(
          child: Text(
            unreadCount == 1
                ? '1 notifica da leggere'
                : '$unreadCount notifiche da leggere',
            style: Theme.of(context).textTheme.titleMedium,
          ),
        ),
        IconButton(
          tooltip: 'Aggiorna',
          onPressed: () {
            ref.invalidate(notificationsProvider);
            ref.invalidate(notificationSummaryProvider);
          },
          icon: const Icon(Icons.refresh),
        ),
        FilledButton.icon(
          onPressed: unreadCount == 0 ? null : () => _markAllRead(context, ref),
          icon: const Icon(Icons.done_all),
          label: const Text('Segna tutto'),
        ),
      ],
    );
  }

  Future<void> _markAllRead(BuildContext context, WidgetRef ref) async {
    try {
      final updatedCount = await ref
          .read(notificationsRepositoryProvider)
          .markAllRead();
      ref.invalidate(notificationsProvider);
      ref.invalidate(notificationSummaryProvider);
      if (!context.mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$updatedCount notifiche aggiornate.')),
      );
    } catch (_) {
      if (!context.mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Notifiche non aggiornate.')),
      );
    }
  }
}

class _NotificationCard extends ConsumerWidget {
  const _NotificationCard({required this.notification});

  final AppNotification notification;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final scheme = Theme.of(context).colorScheme;
    final color = notification.isRead ? scheme.outline : scheme.primary;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(_iconFor(notification.type), color: color),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          notification.title,
                          style: Theme.of(context).textTheme.titleMedium
                              ?.copyWith(fontWeight: FontWeight.w700),
                        ),
                      ),
                      if (!notification.isRead)
                        Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: scheme.primary,
                            shape: BoxShape.circle,
                          ),
                        ),
                    ],
                  ),
                  if (notification.body.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(notification.body),
                  ],
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      _NotificationChip(label: _labelFor(notification.type)),
                      if (notification.createdAt != null)
                        _NotificationChip(
                          label: _formatDate(notification.createdAt!),
                        ),
                    ],
                  ),
                ],
              ),
            ),
            if (!notification.isRead)
              IconButton(
                tooltip: 'Segna letta',
                onPressed: () => _markRead(context, ref),
                icon: const Icon(Icons.done),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _markRead(BuildContext context, WidgetRef ref) async {
    try {
      await ref.read(notificationsRepositoryProvider).markRead(notification.id);
      ref.invalidate(notificationsProvider);
      ref.invalidate(notificationSummaryProvider);
    } catch (_) {
      if (!context.mounted) {
        return;
      }
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Notifica non aggiornata.')));
    }
  }

  IconData _iconFor(String type) {
    return switch (type) {
      'conversation_post_created' => Icons.chat_bubble_outline,
      'case_share_request_created' => Icons.ios_share_outlined,
      'case_share_request_accepted' => Icons.check_circle_outline,
      'case_share_request_rejected' => Icons.cancel_outlined,
      'case_share_request_revoked' => Icons.link_off_outlined,
      'appointment_created' => Icons.event_outlined,
      'appointment_status_changed' => Icons.event_available_outlined,
      'maintenance_reminder_due' => Icons.home_repair_service_outlined,
      _ => Icons.notifications_outlined,
    };
  }

  String _labelFor(String type) {
    return switch (type) {
      'conversation_post_created' => 'Messaggio',
      'case_share_request_created' => 'Condivisione',
      'case_share_request_accepted' => 'Accettata',
      'case_share_request_rejected' => 'Rifiutata',
      'case_share_request_revoked' => 'Revocata',
      'appointment_created' => 'Appuntamento',
      'appointment_status_changed' => 'Agenda',
      'maintenance_reminder_due' => 'Promemoria',
      _ => 'Sistema',
    };
  }

  String _formatDate(DateTime value) {
    final day = value.day.toString().padLeft(2, '0');
    final month = value.month.toString().padLeft(2, '0');
    final hour = value.hour.toString().padLeft(2, '0');
    final minute = value.minute.toString().padLeft(2, '0');
    return '$day/$month $hour:$minute';
  }
}

class _NotificationChip extends StatelessWidget {
  const _NotificationChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        child: Text(label, style: Theme.of(context).textTheme.labelMedium),
      ),
    );
  }
}

class _EmptyNotifications extends StatelessWidget {
  const _EmptyNotifications();

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(Icons.notifications_none, color: Theme.of(context).hintColor),
            const SizedBox(width: 12),
            const Expanded(child: Text('Nessuna notifica.')),
          ],
        ),
      ),
    );
  }
}

class _NotificationsError extends StatelessWidget {
  const _NotificationsError({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(
              Icons.notifications_off_outlined,
              color: Theme.of(context).colorScheme.error,
            ),
            const SizedBox(width: 12),
            const Expanded(child: Text('Notifiche non disponibili.')),
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

class _NotificationsLoading extends StatelessWidget {
  const _NotificationsLoading();

  @override
  Widget build(BuildContext context) {
    return const Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Row(
          children: [
            SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            SizedBox(width: 12),
            Expanded(child: Text('Caricamento notifiche')),
          ],
        ),
      ),
    );
  }
}
