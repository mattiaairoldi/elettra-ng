import 'dart:typed_data';

import 'package:elettra_mobile/app/elettra_app.dart';
import 'package:elettra_mobile/core/i18n/diagnostic_labels.dart';
import 'package:elettra_mobile/core/storage/token_store.dart';
import 'package:elettra_mobile/features/auth/data/auth_models.dart';
import 'package:elettra_mobile/features/auth/data/auth_repository.dart';
import 'package:elettra_mobile/features/auth/presentation/email_verification_screen.dart';
import 'package:elettra_mobile/features/guest/data/guest_models.dart';
import 'package:elettra_mobile/features/guest/data/guest_repository.dart';
import 'package:elettra_mobile/features/health/data/health_repository.dart';
import 'package:elettra_mobile/features/home/data/home_models.dart';
import 'package:elettra_mobile/features/home/data/home_repository.dart';
import 'package:elettra_mobile/features/notifications/data/notification_models.dart';
import 'package:elettra_mobile/features/notifications/data/notification_repository.dart';
import 'package:elettra_mobile/features/problems/data/problem_models.dart';
import 'package:elettra_mobile/features/problems/data/problems_repository.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeHealthRepository implements HealthRepository {
  @override
  Future<HealthStatus> fetchHealth() async {
    return const HealthStatus(status: 'ok');
  }
}

class _FakeTokenStore implements TokenStore {
  String? _guestToken;

  @override
  Future<void> clearTokens() async {}

  @override
  Future<void> clearGuestToken() async {
    _guestToken = null;
  }

  @override
  Future<String?> readAccessToken() async => null;

  @override
  Future<String?> readGuestToken() async => _guestToken;

  @override
  Future<AuthTokens?> readTokens() async => null;

  @override
  Future<void> saveGuestToken(String token) async {
    _guestToken = token;
  }

  @override
  Future<void> saveTokens(AuthTokens tokens) async {}
}

class _FakeAuthRepository implements AuthRepository {
  String? registeredEmail;
  String? verifiedToken;

  @override
  Future<RegisterResult> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
  }) async {
    registeredEmail = email;
    return RegisterResult(
      user: AppUser(
        id: 20,
        email: email,
        firstName: firstName,
        lastName: lastName,
        role: 'customer',
      ),
      detail: 'User created successfully. Verification email sent.',
    );
  }

  @override
  Future<LoginResult> login({
    required String email,
    required String password,
  }) async {
    return LoginResult(
      user: AppUser(
        id: 20,
        email: email,
        firstName: 'Demo',
        lastName: 'User',
        role: 'customer',
        emailVerified: true,
      ),
      tokens: const AuthTokens(
        access: 'access',
        refresh: 'refresh',
        tokenType: 'Bearer',
        accessExpiresIn: 900,
        refreshExpiresIn: 1209600,
      ),
    );
  }

  @override
  Future<VerifyEmailResult> verifyEmail({required String token}) async {
    verifiedToken = token;
    return VerifyEmailResult(
      user: const AppUser(
        id: 20,
        email: 'registered@example.com',
        firstName: 'Registered',
        lastName: 'User',
        role: 'customer',
        emailVerified: true,
      ),
      detail: 'Email verified successfully.',
    );
  }

  @override
  Future<AppUser> currentUser() async {
    return const AppUser(
      id: 20,
      email: 'registered@example.com',
      firstName: 'Registered',
      lastName: 'User',
      role: 'customer',
      emailVerified: true,
    );
  }

  @override
  Future<void> logout(String refreshToken) async {}
}

class _FakeProblemsRepository implements ProblemsRepository {
  final List<CustomerProblem> _createdProblems = [];

  @override
  Future<List<CustomerProblem>> fetchProblems() async {
    return [
      const CustomerProblem(
        id: 1,
        categoryId: 1,
        propertyId: 1,
        assetId: 1,
        title: 'Salvavita abbassato',
        description: 'Il quadro elettrico scatta quando accendo il forno.',
        status: 'open',
        priority: 'normal',
        createdAt: null,
        updatedAt: null,
      ),
      const CustomerProblem(
        id: 2,
        categoryId: 1,
        propertyId: null,
        assetId: null,
        title: 'Diagnosi ospite',
        description: 'Problema elettrico.',
        status: 'in_diagnosis',
        priority: 'normal',
        createdAt: null,
        updatedAt: null,
      ),
      ..._createdProblems,
    ];
  }

  @override
  Future<CustomerProblem> fetchProblem(int problemId) async {
    return (await fetchProblems()).firstWhere(
      (problem) => problem.id == problemId,
    );
  }

  @override
  Future<List<ProblemCategory>> fetchCategories() async {
    return const [
      ProblemCategory(id: 1, name: 'Elettricita', slug: 'elettricita'),
      ProblemCategory(id: 2, name: 'Idraulica', slug: 'idraulica'),
    ];
  }

  @override
  Future<CustomerProblem> createProblemFromDiagnosis({
    required int categoryId,
    required String title,
    required String description,
    required String priority,
  }) async {
    final problem = CustomerProblem(
      id: 100 + _createdProblems.length,
      categoryId: categoryId,
      propertyId: null,
      assetId: null,
      title: title,
      description: description,
      status: 'in_diagnosis',
      priority: priority,
      createdAt: null,
      updatedAt: null,
    );
    _createdProblems.add(problem);
    return problem;
  }

  @override
  Future<List<DiagnosticChapter>> fetchDiagnosticChapters({
    int? categoryId,
  }) async {
    return const [
      DiagnosticChapter(
        id: 1,
        name: 'Controlli iniziali',
        description: 'Verifiche sicure prima del tecnico.',
        categoryId: 1,
        options: [
          DiagnosticChapterOption(
            id: 1,
            chapterId: 1,
            label: 'Scatta subito',
            description: '',
            promptHint: '',
          ),
        ],
      ),
    ];
  }

  @override
  Future<List<DiagnosticAdviceStep>> fetchAdviceSteps({
    required int chapterId,
    int? optionId,
  }) async {
    return const [
      DiagnosticAdviceStep(
        id: 1,
        chapterId: 1,
        chapterOptionId: null,
        title: 'Scollega il forno',
        body: 'Prova a riarmare il quadro con il forno scollegato.',
        safetyLevel: 'low',
        resolutionPrompt: 'Il problema e risolto?',
        nextActions: ['Continua con la diagnosi'],
      ),
    ];
  }

  @override
  Future<DiagnosticFeedbackResult> sendAdviceFeedback({
    required int stepId,
    required int caseId,
    required bool resolved,
    required String note,
  }) async {
    return DiagnosticFeedbackResult(
      caseId: caseId,
      resolved: resolved,
      caseStatus: resolved ? 'resolved' : 'in_diagnosis',
      nextActions: const ['Diagnostica aggiornata'],
    );
  }

  @override
  Future<AiSessionSummary> createAiSession({required int caseId}) async {
    return AiSessionSummary(id: 1, caseId: caseId, status: 'active');
  }

  @override
  Future<List<AiMessage>> fetchAiMessages(int sessionId) async {
    return const [
      AiMessage(
        id: 2,
        role: 'assistant',
        content: 'Il forno potrebbe avere una dispersione.',
        status: 'completed',
      ),
    ];
  }

  @override
  Future<DiagnosticTurnResult> sendDiagnosticTurn({
    required int sessionId,
    required String content,
    int? chapterId,
    int? optionId,
  }) async {
    return const DiagnosticTurnResult(
      userMessage: AiMessage(
        id: 1,
        role: 'user',
        content: 'Succede con il forno acceso.',
        status: 'completed',
      ),
      assistantMessage: AiMessage(
        id: 2,
        role: 'assistant',
        content: 'Il forno potrebbe avere una dispersione.',
        status: 'completed',
      ),
      snapshot: AiDiagnosticSnapshot(
        summary: 'Scatto collegato al forno.',
        riskLevel: 'medium',
        nextQuestion: '',
        escalationRecommended: true,
        escalationReason: 'Serve verifica elettrica.',
        recommendation: 'Condividi il caso con un tecnico.',
      ),
    );
  }

  @override
  Future<List<ProfessionalProfileSummary>> fetchProfessionals({
    int? categoryId,
  }) async {
    return const [
      ProfessionalProfileSummary(
        id: 1,
        displayName: 'Mario Rossi',
        bio: 'Elettricista abilitato.',
        serviceAreaText: 'Milano',
        recipientOrganizationId: 2,
        recipientMembershipId: 3,
        categoryIds: [1],
      ),
    ];
  }

  @override
  Future<CaseShareRequestSummary> shareCase({
    required int caseId,
    required ProfessionalProfileSummary professional,
    required String title,
    required String summary,
  }) async {
    return const CaseShareRequestSummary(
      id: 1,
      status: 'pending',
      shareScope: 'summary',
    );
  }
}

class _FakeGuestRepository implements GuestRepository {
  @override
  Future<void> clearSession() async {}

  @override
  Future<GuestSessionSummary> currentOrStartSession() async {
    return startSession();
  }

  @override
  Future<GuestDiagnosticResult> sendDiagnosticTurn({
    required String message,
    int? chapterId,
    int? optionId,
    bool useAi = true,
  }) async {
    return const GuestDiagnosticResult(
      adviceSteps: [
        DiagnosticAdviceStep(
          id: 1,
          chapterId: 1,
          chapterOptionId: null,
          title: 'Scollega il forno',
          body: 'Prova a riarmare il quadro con il forno scollegato.',
          safetyLevel: 'low',
          resolutionPrompt: 'Il problema e risolto?',
          nextActions: ['Continua con la diagnosi'],
        ),
      ],
      userMessage: AiMessage(
        id: 1,
        role: 'user',
        content: 'Il salvavita scatta.',
        status: 'completed',
      ),
      assistantMessage: AiMessage(
        id: 2,
        role: 'assistant',
        content: 'Ho registrato la descrizione.',
        status: 'completed',
      ),
      snapshot: AiDiagnosticSnapshot(
        summary: 'Problema elettrico.',
        riskLevel: 'medium',
        nextQuestion: 'Succede in una sola stanza?',
        escalationRecommended: false,
        escalationReason: '',
        recommendation: 'Continua con verifiche sicure.',
      ),
      quotas: GuestQuota(
        aiTurnLimit: 2,
        aiTurnsUsed: 1,
        aiTurnsRemaining: 1,
        messageLimit: 8,
        messagesUsed: 2,
        messagesRemaining: 6,
      ),
      callToAction: GuestCallToAction(
        code: '',
        title: '',
        message: '',
        actionLabel: 'Accedi',
      ),
    );
  }

  @override
  Future<GuestPromotionResult> promote({
    required String email,
    required String password,
    String firstName = '',
    String lastName = '',
    int? categoryId,
    String? caseTitle,
    String? caseDescription,
  }) async {
    return const GuestPromotionResult(
      user: AppUser(
        id: 10,
        email: 'guest@example.com',
        firstName: 'Guest',
        lastName: 'User',
        role: 'customer',
      ),
      tokens: AuthTokens(
        access: 'access',
        refresh: 'refresh',
        tokenType: 'Bearer',
        accessExpiresIn: 300,
        refreshExpiresIn: 86400,
      ),
      problem: CustomerProblem(
        id: 2,
        categoryId: 1,
        propertyId: null,
        assetId: null,
        title: 'Diagnosi ospite',
        description: 'Problema elettrico.',
        status: 'in_diagnosis',
        priority: 'normal',
        createdAt: null,
        updatedAt: null,
      ),
      snapshot: AiDiagnosticSnapshot(
        summary: 'Problema elettrico.',
        riskLevel: 'medium',
        nextQuestion: '',
        escalationRecommended: false,
        escalationReason: '',
        recommendation: '',
      ),
    );
  }

  @override
  Future<GuestSessionSummary> startSession() async {
    return const GuestSessionSummary(
      id: 'guest-id',
      token: 'guest-token',
      status: 'active',
      expiresAt: null,
      quotas: GuestQuota(
        aiTurnLimit: 2,
        aiTurnsUsed: 0,
        aiTurnsRemaining: 2,
        messageLimit: 8,
        messagesUsed: 0,
        messagesRemaining: 8,
      ),
    );
  }
}

class _FakeHomeRepository implements HomeRepository {
  _FakeHomeRepository({HomeOverview? initialOverview})
    : _overview = initialOverview ?? _defaultOverview;

  static const _defaultOverview = HomeOverview(
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

  HomeOverview _overview;
  String? createdPropertyName;

  @override
  Future<HomeOverview> fetchOverview() async {
    return _overview;
  }

  @override
  Future<void> createProperty({
    required String name,
    required String addressText,
    required String city,
    required String notes,
  }) async {
    createdPropertyName = name;
    _overview = HomeOverview(
      properties: [
        HomeProperty(
          id: 10,
          name: name,
          addressText: addressText,
          city: city,
          notes: notes,
        ),
      ],
      assets: const [],
      categories: _overview.categories,
      eventsByAssetId: const {},
      remindersByAssetId: const {},
      attachmentsByAssetId: const {},
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

class _FakeNotificationsRepository implements NotificationsRepository {
  _FakeNotificationsRepository({List<AppNotification>? initialNotifications})
    : _notifications = [...?initialNotifications];

  final List<AppNotification> _notifications;

  @override
  Future<List<AppNotification>> fetchNotifications({
    bool unreadOnly = false,
  }) async {
    return [
      for (final item in _notifications)
        if (!unreadOnly || !item.isRead) item,
    ];
  }

  @override
  Future<NotificationSummary> fetchSummary() async {
    return NotificationSummary(
      unreadCount: _notifications.where((item) => !item.isRead).length,
    );
  }

  @override
  Future<AppNotification> markRead(int notificationId) async {
    final index = _notifications.indexWhere(
      (item) => item.id == notificationId,
    );
    if (index < 0) {
      throw StateError('Notification not found');
    }
    _notifications[index] = _copyNotification(
      _notifications[index],
      isRead: true,
      readAt: DateTime(2026, 5, 9, 18, 45),
    );
    return _notifications[index];
  }

  @override
  Future<int> markAllRead() async {
    var updatedCount = 0;
    for (var index = 0; index < _notifications.length; index += 1) {
      if (_notifications[index].isRead) {
        continue;
      }
      updatedCount += 1;
      _notifications[index] = _copyNotification(
        _notifications[index],
        isRead: true,
        readAt: DateTime(2026, 5, 9, 18, 45),
      );
    }
    return updatedCount;
  }

  AppNotification _copyNotification(
    AppNotification notification, {
    required bool isRead,
    required DateTime readAt,
  }) {
    return AppNotification(
      id: notification.id,
      recipientUserId: notification.recipientUserId,
      actorUserId: notification.actorUserId,
      type: notification.type,
      title: notification.title,
      body: notification.body,
      priority: notification.priority,
      targetType: notification.targetType,
      targetId: notification.targetId,
      deepLink: notification.deepLink,
      metadata: notification.metadata,
      isRead: isRead,
      readAt: readAt,
      createdAt: notification.createdAt,
      updatedAt: DateTime(2026, 5, 9, 18, 45),
    );
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
        emailVerified: true,
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
  test('localizes diagnostic risk levels in Italian', () {
    expect(diagnosticRiskLevelLabel('unknown'), 'Non determinato');
    expect(diagnosticRiskLevelLabel('low'), 'Basso');
    expect(diagnosticRiskLevelLabel('medium'), 'Medio');
    expect(diagnosticRiskLevelLabel('high'), 'Alto');
    expect(diagnosticRiskLevelLabel('urgent'), 'Urgente');
    expect(diagnosticRiskLevelLabel('unexpected'), 'Non determinato');
  });

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

  testWidgets('registers user and asks email confirmation', (tester) async {
    final authRepository = _FakeAuthRepository();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authRepositoryProvider.overrideWithValue(authRepository),
          healthRepositoryProvider.overrideWithValue(_FakeHealthRepository()),
          tokenStoreProvider.overrideWithValue(_FakeTokenStore()),
        ],
        child: const ElettraApp(),
      ),
    );

    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(OutlinedButton, 'Registrati'));
    await tester.pumpAndSettle();

    await tester.enterText(find.widgetWithText(TextField, 'Nome'), 'Mario');
    await tester.enterText(find.widgetWithText(TextField, 'Cognome'), 'Rossi');
    await tester.enterText(
      find.widgetWithText(TextField, 'Email'),
      'mario@example.com',
    );
    await tester.enterText(
      find.widgetWithText(TextField, 'Password'),
      'Password123!',
    );
    await tester.tap(find.text('Crea account'));
    await tester.pumpAndSettle();

    expect(authRepository.registeredEmail, 'mario@example.com');
    expect(find.text('Controlla la tua email'), findsOneWidget);
    expect(
      find.textContaining(
        'Abbiamo inviato il link di conferma a mario@example.com',
      ),
      findsOneWidget,
    );
    expect(find.text('Vai al login'), findsOneWidget);
  });

  testWidgets('confirms email token from verification link', (tester) async {
    final authRepository = _FakeAuthRepository();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authRepositoryProvider.overrideWithValue(authRepository),
          healthRepositoryProvider.overrideWithValue(_FakeHealthRepository()),
        ],
        child: const MaterialApp(
          home: EmailVerificationScreen(token: 'email-token'),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(authRepository.verifiedToken, 'email-token');
    expect(find.text('Email confermata'), findsOneWidget);
    expect(
      find.text('Abbiamo confermato la tua email. Ora puoi accedere.'),
      findsOneWidget,
    );
    expect(find.text('Vai al login'), findsOneWidget);
  });

  testWidgets('shows customer home when authenticated', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          healthRepositoryProvider.overrideWithValue(_FakeHealthRepository()),
          homeRepositoryProvider.overrideWithValue(_FakeHomeRepository()),
          notificationsRepositoryProvider.overrideWithValue(
            _FakeNotificationsRepository(),
          ),
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

  testWidgets('creates first home from empty home state', (tester) async {
    final homeRepository = _FakeHomeRepository(
      initialOverview: const HomeOverview(
        properties: [],
        assets: [],
        categories: [
          HomeCategory(
            id: 1,
            name: 'Elettrodomestici',
            slug: 'elettrodomestici',
          ),
        ],
        eventsByAssetId: {},
        remindersByAssetId: {},
        attachmentsByAssetId: {},
      ),
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          healthRepositoryProvider.overrideWithValue(_FakeHealthRepository()),
          homeRepositoryProvider.overrideWithValue(homeRepository),
          notificationsRepositoryProvider.overrideWithValue(
            _FakeNotificationsRepository(),
          ),
          problemsRepositoryProvider.overrideWithValue(
            _FakeProblemsRepository(),
          ),
          authSessionProvider.overrideWith(_AuthenticatedSessionNotifier.new),
        ],
        child: const ElettraApp(),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Nessuna casa registrata'), findsOneWidget);
    await tester.tap(find.text('Aggiungi casa'));
    await tester.pumpAndSettle();

    await tester.enterText(find.widgetWithText(TextField, 'Nome'), 'Casa Mia');
    await tester.enterText(
      find.widgetWithText(TextField, 'Indirizzo'),
      'Via Roma 10',
    );
    await tester.enterText(find.widgetWithText(TextField, 'Città'), 'Torino');
    await tester.tap(find.text('Salva'));
    await tester.pumpAndSettle();

    expect(homeRepository.createdPropertyName, 'Casa Mia');
    expect(find.text('Casa Mia'), findsOneWidget);
    expect(
      find.text('Nessun asset registrato per questo immobile.'),
      findsOneWidget,
    );
    expect(find.text('Aggiungi asset'), findsOneWidget);
  });

  testWidgets('opens problem detail with diagnostics and sharing', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          healthRepositoryProvider.overrideWithValue(_FakeHealthRepository()),
          homeRepositoryProvider.overrideWithValue(_FakeHomeRepository()),
          notificationsRepositoryProvider.overrideWithValue(
            _FakeNotificationsRepository(),
          ),
          problemsRepositoryProvider.overrideWithValue(
            _FakeProblemsRepository(),
          ),
          authSessionProvider.overrideWith(_AuthenticatedSessionNotifier.new),
        ],
        child: const ElettraApp(),
      ),
    );

    await tester.pumpAndSettle();
    await tester.tap(find.text('Problemi'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Salvavita abbassato'));
    await tester.pumpAndSettle();

    expect(find.text('Diagnostica guidata'), findsOneWidget);
    expect(find.text('Controlli iniziali'), findsOneWidget);
    expect(find.text('Scollega il forno'), findsOneWidget);
    expect(find.text('AI diagnostica'), findsOneWidget);
    expect(find.text('Tecnici disponibili'), findsOneWidget);
    expect(find.text('Mario Rossi'), findsOneWidget);
  });

  testWidgets('opens technicians tab with filter and problem shortcut', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          healthRepositoryProvider.overrideWithValue(_FakeHealthRepository()),
          homeRepositoryProvider.overrideWithValue(_FakeHomeRepository()),
          notificationsRepositoryProvider.overrideWithValue(
            _FakeNotificationsRepository(),
          ),
          problemsRepositoryProvider.overrideWithValue(
            _FakeProblemsRepository(),
          ),
          authSessionProvider.overrideWith(_AuthenticatedSessionNotifier.new),
        ],
        child: const ElettraApp(),
      ),
    );

    await tester.pumpAndSettle();
    await tester.tap(find.text('Tecnici').last);
    await tester.pumpAndSettle();

    expect(find.text('Filtro tecnici'), findsOneWidget);
    expect(find.text('Tecnici disponibili'), findsOneWidget);
    expect(find.text('Mario Rossi'), findsOneWidget);
    expect(find.text('Milano'), findsOneWidget);
    expect(find.text('Elettricita'), findsOneWidget);

    final problemsShortcut = find.widgetWithText(TextButton, 'Vai ai problemi');
    await tester.ensureVisible(problemsShortcut);
    await tester.pumpAndSettle();
    await tester.drag(find.byType(ListView), const Offset(0, -160));
    await tester.pumpAndSettle();
    await tester.tap(problemsShortcut);
    await tester.pumpAndSettle();

    expect(find.text('Problemi da risolvere'), findsOneWidget);
    expect(find.text('Salvavita abbassato'), findsOneWidget);
  });

  testWidgets('opens profile tab with account status and logout', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          healthRepositoryProvider.overrideWithValue(_FakeHealthRepository()),
          homeRepositoryProvider.overrideWithValue(_FakeHomeRepository()),
          notificationsRepositoryProvider.overrideWithValue(
            _FakeNotificationsRepository(),
          ),
          tokenStoreProvider.overrideWithValue(_FakeTokenStore()),
          problemsRepositoryProvider.overrideWithValue(
            _FakeProblemsRepository(),
          ),
          authRepositoryProvider.overrideWithValue(_FakeAuthRepository()),
          authSessionProvider.overrideWith(_AuthenticatedSessionNotifier.new),
        ],
        child: const ElettraApp(),
      ),
    );

    await tester.pumpAndSettle();
    await tester.tap(find.text('Profilo').last);
    await tester.pumpAndSettle();

    expect(find.text('Profilo'), findsWidgets);
    expect(find.text('Demo Customer'), findsWidgets);
    expect(find.text('demo.customer@example.com'), findsWidgets);
    expect(find.text('Email confermata'), findsOneWidget);
    expect(find.text('Cliente'), findsWidgets);
    expect(find.text('Notifiche'), findsOneWidget);
    expect(find.text('Push native'), findsOneWidget);

    final refreshButton = find.widgetWithText(
      OutlinedButton,
      'Aggiorna profilo',
    );
    await tester.ensureVisible(refreshButton);
    await tester.pumpAndSettle();
    await tester.tap(refreshButton);
    await tester.pumpAndSettle();
    await tester.drag(find.byType(ListView), const Offset(0, 900));
    await tester.pumpAndSettle();

    expect(find.text('Registered User'), findsWidgets);
    expect(find.text('registered@example.com'), findsWidgets);

    final logoutButton = find.widgetWithText(FilledButton, 'Esci').last;
    await tester.ensureVisible(logoutButton);
    await tester.pumpAndSettle();
    await tester.tap(logoutButton);
    await tester.pumpAndSettle();
    expect(find.text('Vuoi uscire da questo dispositivo?'), findsOneWidget);
    await tester.tap(find.widgetWithText(FilledButton, 'Esci').last);
    await tester.pumpAndSettle();

    expect(find.text('Accedi'), findsWidgets);
  });

  testWidgets('starts authenticated diagnosis and opens created problem', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          healthRepositoryProvider.overrideWithValue(_FakeHealthRepository()),
          homeRepositoryProvider.overrideWithValue(_FakeHomeRepository()),
          notificationsRepositoryProvider.overrideWithValue(
            _FakeNotificationsRepository(),
          ),
          problemsRepositoryProvider.overrideWithValue(
            _FakeProblemsRepository(),
          ),
          authSessionProvider.overrideWith(_AuthenticatedSessionNotifier.new),
        ],
        child: const ElettraApp(),
      ),
    );

    await tester.pumpAndSettle();
    await tester.tap(find.text('Diagnosi').last);
    await tester.pumpAndSettle();

    expect(find.text('Nuova diagnosi'), findsOneWidget);
    expect(find.text('Controlli iniziali'), findsOneWidget);

    await tester.enterText(
      find.widgetWithText(TextField, 'Titolo'),
      'Diagnosi salvavita',
    );
    await tester.enterText(
      find.widgetWithText(TextField, 'Descrizione'),
      'Il salvavita scatta quando accendo il forno.',
    );
    final submitButton = find.widgetWithText(FilledButton, 'Avvia diagnosi');
    await tester.ensureVisible(submitButton);
    await tester.pumpAndSettle();
    await tester.tap(submitButton);
    await tester.pumpAndSettle();

    expect(find.text('Problemi da risolvere'), findsOneWidget);
    expect(find.text('Diagnosi salvavita'), findsOneWidget);
    expect(find.text('AI diagnostica'), findsOneWidget);
    expect(
      find.text('Il forno potrebbe avere una dispersione.'),
      findsOneWidget,
    );
  });

  testWidgets('opens notification center and marks notification read', (
    tester,
  ) async {
    final notificationsRepository = _FakeNotificationsRepository(
      initialNotifications: [
        AppNotification(
          id: 1,
          recipientUserId: 1,
          actorUserId: 2,
          type: 'conversation_post_created',
          title: 'Nuovo messaggio',
          body: 'Hai un nuovo messaggio in una conversazione.',
          priority: 'normal',
          targetType: 'conversation',
          targetId: '1',
          deepLink: 'elettra://conversations/1',
          metadata: const {},
          isRead: false,
          readAt: null,
          createdAt: DateTime(2026, 5, 9, 18, 30),
          updatedAt: DateTime(2026, 5, 9, 18, 30),
        ),
      ],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          healthRepositoryProvider.overrideWithValue(_FakeHealthRepository()),
          homeRepositoryProvider.overrideWithValue(_FakeHomeRepository()),
          notificationsRepositoryProvider.overrideWithValue(
            notificationsRepository,
          ),
          problemsRepositoryProvider.overrideWithValue(
            _FakeProblemsRepository(),
          ),
          authSessionProvider.overrideWith(_AuthenticatedSessionNotifier.new),
        ],
        child: const ElettraApp(),
      ),
    );

    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('Notifiche'));
    await tester.pumpAndSettle();

    expect(find.text('Notifiche'), findsOneWidget);
    expect(find.text('1 notifica da leggere'), findsOneWidget);
    expect(find.text('Nuovo messaggio'), findsOneWidget);
    expect(
      find.text('Hai un nuovo messaggio in una conversazione.'),
      findsOneWidget,
    );

    await tester.tap(find.byTooltip('Segna letta'));
    await tester.pumpAndSettle();

    expect(find.text('0 notifiche da leggere'), findsOneWidget);
  });

  testWidgets('starts guest diagnostic from login', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          healthRepositoryProvider.overrideWithValue(_FakeHealthRepository()),
          homeRepositoryProvider.overrideWithValue(_FakeHomeRepository()),
          notificationsRepositoryProvider.overrideWithValue(
            _FakeNotificationsRepository(),
          ),
          tokenStoreProvider.overrideWithValue(_FakeTokenStore()),
          problemsRepositoryProvider.overrideWithValue(
            _FakeProblemsRepository(),
          ),
          guestRepositoryProvider.overrideWithValue(_FakeGuestRepository()),
        ],
        child: const ElettraApp(),
      ),
    );

    await tester.pumpAndSettle();
    await tester.tap(find.text('Continua come ospite'));
    await tester.pumpAndSettle();

    expect(find.text('Diagnosi ospite'), findsOneWidget);
    expect(find.text('Controlli iniziali'), findsOneWidget);
    expect(find.text('AI 2/2'), findsOneWidget);

    await tester.enterText(
      find.widgetWithText(TextField, 'Descrivi il problema'),
      'Il salvavita scatta.',
    );
    await tester.ensureVisible(find.text('Avvia diagnosi'));
    await tester.tap(find.text('Avvia diagnosi'));
    await tester.pumpAndSettle();
    await tester.drag(find.byType(ListView), const Offset(0, -500));
    await tester.pumpAndSettle();

    expect(find.text('Consigli guidati'), findsOneWidget);
    expect(find.text('Scollega il forno'), findsOneWidget);
    expect(find.text('Ho registrato la descrizione.'), findsOneWidget);

    await tester.ensureVisible(find.text('Salva come pratica'));
    await tester.tap(find.text('Salva come pratica'));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.widgetWithText(TextField, 'Email'),
      'guest@example.com',
    );
    await tester.enterText(
      find.widgetWithText(TextField, 'Password'),
      'Password123!',
    );
    await tester.tap(find.text('Crea account e salva'));
    await tester.pumpAndSettle();

    expect(find.text('Problemi da risolvere'), findsOneWidget);
    expect(find.text('Diagnosi ospite'), findsOneWidget);
    expect(find.text('AI diagnostica'), findsOneWidget);
  });
}
