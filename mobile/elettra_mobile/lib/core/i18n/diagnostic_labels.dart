String diagnosticRiskLevelLabel(String riskLevel) {
  return switch (riskLevel.trim().toLowerCase()) {
    'unknown' => 'Non determinato',
    'low' => 'Basso',
    'medium' => 'Medio',
    'high' => 'Alto',
    'urgent' => 'Urgente',
    _ => 'Non determinato',
  };
}
