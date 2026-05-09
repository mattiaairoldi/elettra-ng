class AppUser {
  const AppUser({
    required this.id,
    required this.email,
    required this.firstName,
    required this.lastName,
    required this.role,
  });

  factory AppUser.fromJson(Map<String, dynamic> json) {
    return AppUser(
      id: json['id'] as int,
      email: json['email']?.toString() ?? '',
      firstName: json['first_name']?.toString() ?? '',
      lastName: json['last_name']?.toString() ?? '',
      role: json['role']?.toString() ?? '',
    );
  }

  final int id;
  final String email;
  final String firstName;
  final String lastName;
  final String role;

  String get displayName {
    final fullName = '$firstName $lastName'.trim();
    return fullName.isEmpty ? email : fullName;
  }
}

class AuthTokens {
  const AuthTokens({
    required this.access,
    required this.refresh,
    required this.tokenType,
    required this.accessExpiresIn,
    required this.refreshExpiresIn,
  });

  factory AuthTokens.fromJson(Map<String, dynamic> json) {
    return AuthTokens(
      access: json['access']?.toString() ?? '',
      refresh: json['refresh']?.toString() ?? '',
      tokenType: json['token_type']?.toString() ?? 'Bearer',
      accessExpiresIn: json['access_expires_in'] as int? ?? 0,
      refreshExpiresIn: json['refresh_expires_in'] as int? ?? 0,
    );
  }

  final String access;
  final String refresh;
  final String tokenType;
  final int accessExpiresIn;
  final int refreshExpiresIn;
}

class AuthSession {
  const AuthSession({
    required this.user,
    required this.tokens,
  });

  final AppUser user;
  final AuthTokens tokens;
}

class LoginResult {
  const LoginResult({
    required this.user,
    required this.tokens,
  });

  factory LoginResult.fromJson(Map<String, dynamic> json) {
    return LoginResult(
      user: AppUser.fromJson(json['user'] as Map<String, dynamic>),
      tokens: AuthTokens.fromJson(json['tokens'] as Map<String, dynamic>),
    );
  }

  final AppUser user;
  final AuthTokens tokens;
}
