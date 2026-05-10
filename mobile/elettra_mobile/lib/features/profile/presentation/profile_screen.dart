import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/data/auth_models.dart';
import '../../auth/data/auth_repository.dart';

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  bool _refreshing = false;
  bool _loggingOut = false;
  String? _errorMessage;

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(authSessionProvider);
    final user = session?.user;

    if (session == null || user == null) {
      return const _MissingSessionPanel();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _IdentityCard(user: user),
        const SizedBox(height: 12),
        _AccountStatusCard(user: user),
        const SizedBox(height: 12),
        _SessionCard(tokens: session.tokens),
        const SizedBox(height: 12),
        _NotificationStatusCard(),
        if (_errorMessage != null) ...[
          const SizedBox(height: 12),
          _ErrorCard(message: _errorMessage!),
        ],
        const SizedBox(height: 12),
        _ProfileActionsCard(
          refreshing: _refreshing,
          loggingOut: _loggingOut,
          onRefresh: _refreshProfile,
          onLogout: _confirmLogout,
        ),
      ],
    );
  }

  Future<void> _refreshProfile() async {
    final session = ref.read(authSessionProvider);
    if (session == null || _refreshing) {
      return;
    }

    setState(() {
      _refreshing = true;
      _errorMessage = null;
    });

    try {
      final user = await ref.read(authRepositoryProvider).currentUser();
      ref
          .read(authSessionProvider.notifier)
          .setSession(AuthSession(user: user, tokens: session.tokens));
    } catch (_) {
      if (!mounted) {
        return;
      }
      setState(() {
        _errorMessage = 'Profilo non aggiornato.';
      });
    } finally {
      if (mounted) {
        setState(() => _refreshing = false);
      }
    }
  }

  Future<void> _confirmLogout() async {
    if (_loggingOut) {
      return;
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Esci'),
        content: const Text('Vuoi uscire da questo dispositivo?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Annulla'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Esci'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) {
      return;
    }

    setState(() {
      _loggingOut = true;
      _errorMessage = null;
    });

    await ref.read(authActionsProvider).logout();
  }
}

class _IdentityCard extends StatelessWidget {
  const _IdentityCard({required this.user});

  final AppUser user;

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 28,
              child: Text(
                _initialsFor(user),
                style: Theme.of(
                  context,
                ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    user.displayName,
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(user.email),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      _StatusChip(
                        icon: Icons.badge_outlined,
                        label: _roleLabel(user.role),
                        emphasized: true,
                      ),
                      _StatusChip(
                        icon: user.emailVerified
                            ? Icons.verified_outlined
                            : Icons.mark_email_unread_outlined,
                        label: user.emailVerified
                            ? 'Email confermata'
                            : 'Email da confermare',
                        emphasized: user.emailVerified,
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AccountStatusCard extends StatelessWidget {
  const _AccountStatusCard({required this.user});

  final AppUser user;

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _PanelTitle(icon: Icons.person_outline, label: 'Account'),
            const SizedBox(height: 12),
            _InfoRow(label: 'Nome', value: user.displayName),
            _InfoRow(label: 'Email', value: user.email),
            _InfoRow(label: 'Ruolo', value: _roleLabel(user.role)),
            _InfoRow(
              label: 'Stato',
              value: user.isActive ? 'Attivo' : 'Disattivato',
            ),
            _InfoRow(
              label: 'Verifica email',
              value: user.emailVerified ? 'Confermata' : 'In attesa',
            ),
          ],
        ),
      ),
    );
  }
}

class _SessionCard extends StatelessWidget {
  const _SessionCard({required this.tokens});

  final AuthTokens tokens;

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _PanelTitle(icon: Icons.lock_outline, label: 'Sessione'),
            const SizedBox(height: 12),
            _InfoRow(label: 'Tipo token', value: tokens.tokenType),
            _InfoRow(
              label: 'Accesso',
              value: _durationLabel(tokens.accessExpiresIn),
            ),
            _InfoRow(
              label: 'Refresh',
              value: _durationLabel(tokens.refreshExpiresIn),
            ),
          ],
        ),
      ),
    );
  }
}

class _NotificationStatusCard extends StatelessWidget {
  const _NotificationStatusCard();

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: const Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _PanelTitle(icon: Icons.notifications_outlined, label: 'Notifiche'),
            SizedBox(height: 12),
            _InfoRow(label: 'In-app', value: 'Attive'),
            _InfoRow(label: 'Push native', value: 'Non configurate'),
          ],
        ),
      ),
    );
  }
}

class _ProfileActionsCard extends StatelessWidget {
  const _ProfileActionsCard({
    required this.refreshing,
    required this.loggingOut,
    required this.onRefresh,
    required this.onLogout,
  });

  final bool refreshing;
  final bool loggingOut;
  final VoidCallback onRefresh;
  final VoidCallback onLogout;

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            OutlinedButton.icon(
              onPressed: refreshing || loggingOut ? null : onRefresh,
              icon: refreshing
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.refresh),
              label: const Text('Aggiorna profilo'),
            ),
            FilledButton.tonalIcon(
              onPressed: refreshing || loggingOut ? null : onLogout,
              icon: loggingOut
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.logout),
              label: const Text('Esci'),
            ),
          ],
        ),
      ),
    );
  }
}

class _MissingSessionPanel extends StatelessWidget {
  const _MissingSessionPanel();

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: const Padding(
        padding: EdgeInsets.all(16),
        child: _PanelTitle(
          icon: Icons.person_off_outlined,
          label: 'Sessione non disponibile',
        ),
      ),
    );
  }
}

class _ErrorCard extends StatelessWidget {
  const _ErrorCard({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      color: scheme.errorContainer,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(Icons.error_outline, color: scheme.onErrorContainer),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                message,
                style: TextStyle(color: scheme.onErrorContainer),
              ),
            ),
          ],
        ),
      ),
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

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 112,
            child: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({
    required this.icon,
    required this.label,
    this.emphasized = false,
  });

  final IconData icon;
  final String label;
  final bool emphasized;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: emphasized ? scheme.primaryContainer : scheme.surfaceContainer,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 16,
              color: emphasized
                  ? scheme.onPrimaryContainer
                  : scheme.onSurfaceVariant,
            ),
            const SizedBox(width: 6),
            Text(
              label,
              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                color: emphasized
                    ? scheme.onPrimaryContainer
                    : scheme.onSurfaceVariant,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

String _initialsFor(AppUser user) {
  final source = user.displayName.trim().isEmpty
      ? user.email
      : user.displayName;
  final parts = source
      .split(RegExp(r'\s+|@'))
      .where((part) => part.isNotEmpty)
      .toList();
  if (parts.isEmpty) {
    return '?';
  }
  return parts.take(2).map((part) => part[0]).join().toUpperCase();
}

String _roleLabel(String role) {
  return switch (role) {
    'customer' => 'Cliente',
    'professional' => 'Tecnico',
    'admin' => 'Admin',
    _ => role.trim().isEmpty ? 'Utente' : role,
  };
}

String _durationLabel(int seconds) {
  if (seconds <= 0) {
    return 'Non disponibile';
  }
  final duration = Duration(seconds: seconds);
  if (duration.inDays >= 1) {
    return '${duration.inDays} giorni';
  }
  if (duration.inHours >= 1) {
    return '${duration.inHours} ore';
  }
  return '${duration.inMinutes} minuti';
}
