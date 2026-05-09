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
  bool _isSubmitting = false;
  bool _showGuestDiagnostic = false;
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
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
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
              'Accedi',
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
                child: Column(
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
                          : () => setState(() => _showGuestDiagnostic = true),
                      icon: const Icon(Icons.manage_search_outlined),
                      label: const Text('Continua come ospite'),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _messageFor(DioException error) {
    final status = error.response?.statusCode;
    if (status == 400 || status == 401) {
      return 'Email o password non corrette.';
    }
    return 'Servizio non raggiungibile.';
  }
}
