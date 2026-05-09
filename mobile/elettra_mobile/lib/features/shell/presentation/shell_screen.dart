import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/data/auth_repository.dart';
import '../../health/presentation/api_status_card.dart';
import '../../home/presentation/home_screen.dart';
import '../../problems/presentation/problems_screen.dart';

class ShellScreen extends ConsumerStatefulWidget {
  const ShellScreen({super.key});

  @override
  ConsumerState<ShellScreen> createState() => _ShellScreenState();
}

class _ShellScreenState extends ConsumerState<ShellScreen> {
  int _selectedIndex = 0;

  static const _destinations = [
    _Destination(
      label: 'Casa',
      title: 'La mia casa',
      icon: Icons.home_work_outlined,
    ),
    _Destination(
      label: 'Problemi',
      title: 'Problemi da risolvere',
      icon: Icons.assignment_outlined,
    ),
    _Destination(label: 'Diagnosi', icon: Icons.forum_outlined),
    _Destination(label: 'Tecnici', icon: Icons.engineering_outlined),
    _Destination(label: 'Profilo', icon: Icons.person_outline),
  ];

  @override
  Widget build(BuildContext context) {
    final destination = _destinations[_selectedIndex];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Elettra'),
        actions: [
          IconButton(
            tooltip: 'Esci',
            onPressed: () => ref.read(authActionsProvider).logout(),
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          children: [
            Text(
              destination.title,
              style: Theme.of(
                context,
              ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            const ApiStatusCard(),
            const SizedBox(height: 16),
            if (_selectedIndex == 0)
              const HomeScreen()
            else if (_selectedIndex == 1)
              const ProblemsScreen()
            else
              _PlaceholderPanel(destination: destination),
          ],
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (index) {
          setState(() => _selectedIndex = index);
        },
        destinations: [
          for (final item in _destinations)
            NavigationDestination(
              icon: Icon(item.icon),
              selectedIcon: Icon(item.icon, fill: 1),
              label: item.label,
            ),
        ],
      ),
    );
  }
}

class _PlaceholderPanel extends StatelessWidget {
  const _PlaceholderPanel({required this.destination});

  final _Destination destination;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(destination.icon, size: 28),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                _copyFor(destination.label),
                style: Theme.of(context).textTheme.bodyLarge,
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _copyFor(String label) {
    return switch (label) {
      'Problemi' => 'Qui collegheremo elenco e dettaglio dei problemi aperti.',
      'Diagnosi' => 'Qui entreranno consigli guidati, feedback e chat AI.',
      'Tecnici' => 'Qui verranno mostrati professionisti e condivisioni.',
      'Casa' => 'Qui verranno mostrati immobili, asset e promemoria.',
      _ => 'Qui entreranno autenticazione, account e preferenze.',
    };
  }
}

class _Destination {
  const _Destination({required this.label, String? title, required this.icon})
    : title = title ?? label;

  final String label;
  final String title;
  final IconData icon;
}
