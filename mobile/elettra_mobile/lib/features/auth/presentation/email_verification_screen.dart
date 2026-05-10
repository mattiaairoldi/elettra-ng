import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../health/presentation/api_status_card.dart';
import '../data/auth_models.dart';
import '../data/auth_repository.dart';

class EmailVerificationScreen extends ConsumerStatefulWidget {
  const EmailVerificationScreen({super.key, required this.token});

  final String token;

  @override
  ConsumerState<EmailVerificationScreen> createState() =>
      _EmailVerificationScreenState();
}

class _EmailVerificationScreenState
    extends ConsumerState<EmailVerificationScreen> {
  Future<VerifyEmailResult>? _verification;

  @override
  void initState() {
    super.initState();
    final token = widget.token.trim();
    if (token.isNotEmpty) {
      _verification = ref
          .read(authRepositoryProvider)
          .verifyEmail(token: token);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Elettra')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          children: [
            Text(
              'Conferma email',
              style: Theme.of(
                context,
              ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            const ApiStatusCard(),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: _buildContent(context),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContent(BuildContext context) {
    final verification = _verification;
    if (verification == null) {
      return _VerificationMessage(
        icon: Icons.error_outline,
        title: 'Link non valido',
        body: 'Il link di conferma non contiene un token valido.',
        actionLabel: 'Vai al login',
        onAction: () => context.go('/'),
      );
    }

    return FutureBuilder<VerifyEmailResult>(
      future: verification,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Padding(
            padding: EdgeInsets.symmetric(vertical: 24),
            child: Center(child: CircularProgressIndicator()),
          );
        }
        if (snapshot.hasError) {
          return _VerificationMessage(
            icon: Icons.error_outline,
            title: 'Link non valido o scaduto',
            body: 'Richiedi una nuova registrazione o riprova dal link email.',
            actionLabel: 'Vai al login',
            onAction: () => context.go('/'),
          );
        }
        return _VerificationMessage(
          icon: Icons.mark_email_read_outlined,
          title: 'Email confermata',
          body: 'Abbiamo confermato la tua email. Ora puoi accedere.',
          actionLabel: 'Vai al login',
          onAction: () => context.go('/'),
        );
      },
    );
  }
}

class _VerificationMessage extends StatelessWidget {
  const _VerificationMessage({
    required this.icon,
    required this.title,
    required this.body,
    required this.actionLabel,
    required this.onAction,
  });

  final IconData icon;
  final String title;
  final String body;
  final String actionLabel;
  final VoidCallback onAction;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: scheme.primary),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                title,
                style: Theme.of(
                  context,
                ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Text(body),
        const SizedBox(height: 16),
        FilledButton.icon(
          onPressed: onAction,
          icon: const Icon(Icons.login),
          label: Text(actionLabel),
        ),
      ],
    );
  }
}
