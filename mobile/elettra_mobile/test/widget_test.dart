import 'dart:typed_data';

import 'package:elettra_mobile/app/elettra_app.dart';
import 'package:elettra_mobile/core/storage/token_store.dart';
import 'package:elettra_mobile/features/auth/data/auth_models.dart';
import 'package:elettra_mobile/features/auth/data/auth_repository.dart';
import 'package:elettra_mobile/features/health/data/health_repository.dart';
import 'package:elettra_mobile/features/home/data/home_models.dart';
import 'package:elettra_mobile/features/home/data/home_repository.dart';
import 'package:elettra_mobile/features/problems/data/problem_models.dart';
import 'package:elettra_mobile/features/problems/data/problems_repository.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeHealthRepository implements HealthRepository {
  @override
  Future<HealthStatus> fetchHealth() async {
    return const HealthStatus(status: 'ok');
  }
}

class _FakeTokenStore implements TokenStore {
  @override
  Future<void> clearTokens() async {}

  @override
  Future<String?> readAccessToken() async => null;

  @override
  Future<AuthTokens?> readTokens() async => null;

  @override
  Future<void> saveTokens(AuthTokens tokens) async {}
}

class _FakeProblemsRepository implements ProblemsRepository {
  @override
  Future<List<CustomerProblem>> fetchProblems() async {
    return const [
      CustomerProblem(
        id: 1,
        title: 'Salvavita abbassato',
        description: 'Il quadro elettrico scatta quando accendo il forno.',
        status: 'open',
        priority: 'normal',
        createdAt: null,
        updatedAt: null,
      ),
    ];
  }
}

class _FakeHomeRepository implements HomeRepository {
  @override
  Future<HomeOverview> fetchOverview() async {
    return const HomeOverview(
      properties: [
        HomeProperty(
          id: 1,
          name: 'Casa Demo',
          addressText: 'Via Demo 1',
          city: 'Milano',
          notes: '',
        ),
      ],
      assets: [
        HomeAsset(
          id: 1,
          propertyId: 1,
          categoryId: 1,
          name: 'Lavatrice',
          description: 'Lavatrice di servizio',
          locationText: 'Bagno',
          metadata: {'manufacturer': 'DemoWash', 'model': 'DW-800'},
        ),
      ],
      categories: [
        HomeCategory(id: 1, name: 'Elettrodomestici', slug: 'elettrodomestici'),
      ],
      eventsByAssetId: {
        1: [
          HomeMaintenanceEvent(
            id: 1,
            assetId: 1,
            propertyId: 1,
            eventType: 'cleaning',
            title: 'Pulizia filtro',
            description: '',
            eventDate: null,
          ),
        ],
      },
      remindersByAssetId: {
        1: [
          HomeMaintenanceReminder(
            id: 1,
            assetId: 1,
            propertyId: 1,
            title: 'Prossima pulizia filtro',
            description: '',
            dueAt: null,
            recurrenceRule: 'quarterly',
            status: 'active',
          ),
        ],
      },
      attachmentsByAssetId: {
        1: [
          HomeAttachment(
            id: 1,
            caseId: null,
            assetId: 1,
            fileUrl: '/media/manuale.pdf',
            fileName: 'manuale-lavatrice.pdf',
            mimeType: 'application/pdf',
            sizeBytes: 1200,
            attachmentType: 'document',
            createdAt: null,
          ),
        ],
      },
    );
  }

  @override
  Future<void> createAsset({
    required int propertyId,
    required int categoryId,
    required String name,
    required String description,
    required String locationText,
    required Map<String, dynamic> metadata,
  }) async {}

  @override
  Future<void> createMaintenanceEvent({
    required int assetId,
    required String eventType,
    required String title,
    required String description,
    required DateTime eventDate,
  }) async {}

  @override
  Future<void> createMaintenanceReminder({
    required int assetId,
    required String title,
    required String description,
    required DateTime dueAt,
    required String recurrenceRule,
  }) async {}

  @override
  Future<void> completeReminder(int reminderId) async {}

  @override
  Future<void> uploadAssetAttachment({
    required int assetId,
    required String fileName,
    required Uint8List bytes,
    required String attachmentType,
  }) async {}

  @override
  Future<int> createProblemFromAsset({
    required int assetId,
    required int categoryId,
    required String title,
    required String description,
    required String priority,
  }) async {
    return 2;
  }
}

class _AuthenticatedSessionNotifier extends AuthSessionNotifier {
  @override
  AuthSession? build() {
    return const AuthSession(
      user: AppUser(
        id: 1,
        email: 'demo.customer@example.com',
        firstName: 'Demo',
        lastName: 'Customer',
        role: 'customer',
      ),
      tokens: AuthTokens(
        access: 'access',
        refresh: 'refresh',
        tokenType: 'Bearer',
        accessExpiresIn: 900,
        refreshExpiresIn: 1209600,
      ),
    );
  }
}

void main() {
  testWidgets('shows login when unauthenticated', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          healthRepositoryProvider.overrideWithValue(_FakeHealthRepository()),
          tokenStoreProvider.overrideWithValue(_FakeTokenStore()),
        ],
        child: const ElettraApp(),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Elettra'), findsOneWidget);
    expect(find.text('Accedi'), findsWidgets);
    expect(find.text('API online'), findsOneWidget);
  });

  testWidgets('shows customer home when authenticated', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          healthRepositoryProvider.overrideWithValue(_FakeHealthRepository()),
          homeRepositoryProvider.overrideWithValue(_FakeHomeRepository()),
          problemsRepositoryProvider.overrideWithValue(
            _FakeProblemsRepository(),
          ),
          authSessionProvider.overrideWith(_AuthenticatedSessionNotifier.new),
        ],
        child: const ElettraApp(),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('La mia casa'), findsOneWidget);
    expect(find.text('Casa'), findsOneWidget);
    expect(find.text('API online'), findsOneWidget);
    expect(find.text('Casa Demo'), findsOneWidget);
    expect(find.text('Lavatrice'), findsOneWidget);
  });
}
