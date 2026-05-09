import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/health_repository.dart';

class ApiStatusCard extends ConsumerWidget {
  const ApiStatusCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final health = ref.watch(healthStatusProvider);
    final scheme = Theme.of(context).colorScheme;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: health.when(
          data: (status) => Row(
            children: [
              Icon(
                status.isOk ? Icons.check_circle : Icons.error_outline,
                color: status.isOk ? Colors.green.shade700 : scheme.error,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  status.isOk ? 'API online' : 'API non pronta',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
            ],
          ),
          error: (error, stackTrace) => Row(
            children: [
              Icon(Icons.cloud_off_outlined, color: scheme.error),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'API non raggiungibile',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
              IconButton(
                tooltip: 'Riprova',
                onPressed: () => ref.invalidate(healthStatusProvider),
                icon: const Icon(Icons.refresh),
              ),
            ],
          ),
          loading: () => const Row(
            children: [
              SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
              SizedBox(width: 12),
              Expanded(child: Text('Verifica API in corso')),
            ],
          ),
        ),
      ),
    );
  }
}
