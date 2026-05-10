import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../guest/presentation/guest_diagnostic_screen.dart';
import '../../health/presentation/api_status_card.dart';
import '../data/auth_repository.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  late final TextEditingController _emailController;
  late final TextEditingController _passwordController;
  late final TextEditingController _firstNameController;
  late final TextEditingController _lastNameController;
  bool _isSubmitting = false;
  bool _showGuestDiagnostic = false;
  bool _showRegistration = false;
  String? _registeredEmail;
  String? _error;

  @override
  void initState() {
    super.initState();
    _emailController = TextEditingController(
      text: kDebugMode ? 'demo.customer@example.com' : '',
    );
    _passwordController = TextEditingController(
      text: kDebugMode ? 'Password123!' : '',
    );
    _firstNameController = TextEditingController();
    _lastNameController = TextEditingController();
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _firstNameController.dispose();
    _lastNameController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_isSubmitting) {
      return;
    }

    setState(() {
      _isSubmitting = true;
      _error = null;
    });

    try {
      await ref
          .read(authActionsProvider)
          .login(
            email: _emailController.text.trim(),
            password: _passwordController.text,
          );
    } on DioException catch (error) {
      setState(() => _error = _messageFor(error));
    } catch (_) {
      setState(() => _error = 'Accesso non riuscito.');
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  Future<void> _submitRegistration() async {
    if (_isSubmitting) {
      return;
    }

    setState(() {
      _isSubmitting = true;
      _error = null;
    });

    final email = _emailController.text.trim();
    try {
      await ref
          .read(authRepositoryProvider)
          .register(
            email: email,
            password: _passwordController.text,
            firstName: _firstNameController.text.trim(),
            lastName: _lastNameController.text.trim(),
          );
      if (mounted) {
        setState(() => _registeredEmail = email);
      }
    } on DioException catch (error) {
      setState(() => _error = _messageFor(error));
    } catch (_) {
      setState(() => _error = 'Registrazione non riuscita.');
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    if (_showGuestDiagnostic) {
      return GuestDiagnosticScreen(
        onBackToLogin: () => setState(() => _showGuestDiagnostic = false),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Elettra')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          children: [
            Text(
              _showRegistration ? 'Registrati' : 'Accedi',
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
                child: _showRegistration
                    ? _buildRegistrationCard(context, scheme)
                    : _buildLoginCard(scheme),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLoginCard(ColorScheme scheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          controller: _emailController,
          keyboardType: TextInputType.emailAddress,
          autofillHints: const [AutofillHints.email],
          decoration: const InputDecoration(
            labelText: 'Email',
            prefixIcon: Icon(Icons.mail_outline),
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _passwordController,
          obscureText: true,
          autofillHints: const [AutofillHints.password],
          decoration: const InputDecoration(
            labelText: 'Password',
            prefixIcon: Icon(Icons.lock_outline),
          ),
          onSubmitted: (_) => _submit(),
        ),
        if (_error != null) ...[
          const SizedBox(height: 12),
          Text(_error!, style: TextStyle(color: scheme.error)),
        ],
        const SizedBox(height: 16),
        FilledButton.icon(
          onPressed: _isSubmitting ? null : _submit,
          icon: _isSubmitting
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.login),
          label: const Text('Accedi'),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: _isSubmitting
              ? null
              : () => setState(() => _showRegistration = true),
          icon: const Icon(Icons.person_add_alt_outlined),
          label: const Text('Registrati'),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: _isSubmitting
              ? null
              : () => setState(() => _showGuestDiagnostic = true),
          icon: const Icon(Icons.manage_search_outlined),
          label: const Text('Continua come ospite'),
        ),
      ],
    );
  }

  Widget _buildRegistrationCard(BuildContext context, ColorScheme scheme) {
    final registeredEmail = _registeredEmail;
    if (registeredEmail != null) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.mark_email_unread_outlined, color: scheme.primary),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'Controlla la tua email',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'Abbiamo inviato il link di conferma a $registeredEmail. Dopo la conferma potrai accedere.',
          ),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: () => setState(() {
              _showRegistration = false;
              _registeredEmail = null;
              _error = null;
            }),
            icon: const Icon(Icons.login),
            label: const Text('Vai al login'),
          ),
        ],
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _firstNameController,
                enabled: !_isSubmitting,
                autofillHints: const [AutofillHints.givenName],
                decoration: const InputDecoration(labelText: 'Nome'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: TextField(
                controller: _lastNameController,
                enabled: !_isSubmitting,
                autofillHints: const [AutofillHints.familyName],
                decoration: const InputDecoration(labelText: 'Cognome'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _emailController,
          enabled: !_isSubmitting,
          keyboardType: TextInputType.emailAddress,
          autofillHints: const [AutofillHints.email],
          decoration: const InputDecoration(
            labelText: 'Email',
            prefixIcon: Icon(Icons.mail_outline),
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _passwordController,
          enabled: !_isSubmitting,
          obscureText: true,
          autofillHints: const [AutofillHints.newPassword],
          decoration: const InputDecoration(
            labelText: 'Password',
            prefixIcon: Icon(Icons.lock_outline),
          ),
          onSubmitted: (_) => _submitRegistration(),
        ),
        if (_error != null) ...[
          const SizedBox(height: 12),
          Text(_error!, style: TextStyle(color: scheme.error)),
        ],
        const SizedBox(height: 16),
        FilledButton.icon(
          onPressed: _isSubmitting ? null : _submitRegistration,
          icon: _isSubmitting
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.person_add_alt_outlined),
          label: const Text('Crea account'),
        ),
        const SizedBox(height: 8),
        TextButton(
          onPressed: _isSubmitting
              ? null
              : () => setState(() {
                  _showRegistration = false;
                  _registeredEmail = null;
                  _error = null;
                }),
          child: const Text('Ho gia un account'),
        ),
      ],
    );
  }

  String _messageFor(DioException error) {
    final status = error.response?.statusCode;
    final message = _firstErrorMessage(error.response?.data);
    if (message != null) {
      if (message == 'Email address is not verified.') {
        return 'Conferma la tua email prima di accedere.';
      }
      if (message == 'A user with this email already exists.') {
        return 'Esiste gia un account con questa email.';
      }
      return message;
    }
    if (status == 400 || status == 401) {
      return 'Email o password non corrette.';
    }
    return 'Servizio non raggiungibile.';
  }

  String? _firstErrorMessage(Object? data) {
    if (data is! Map<String, dynamic>) {
      return null;
    }
    for (final key in ['detail', 'email', 'password', 'non_field_errors']) {
      final value = data[key];
      if (value is String && value.isNotEmpty) {
        return value;
      }
      if (value is List && value.isNotEmpty) {
        return value.first.toString();
      }
    }
    return null;
  }
}
