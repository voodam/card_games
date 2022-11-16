requirements = {
  # cost tech_level energy armor radius prerequisites
  ConstructionYard: (None, 1, 20, 100, 4),
  WindTrap:         (225,  1, 100, 35, 2),
  Refinery:         (1500, 1, 50, 60, 3, WindTrap),
  Barracks:         (225,  2, 15, 35, 4, WindTrap),
  LightFactory:     (500,  2, 40, 45, 3, Refinery),
  HeavyFactory:     (1000, 4, 60, 60, 3, Refinery),
  Outpost:          (750,  6, 30, 60, 7, Barracks),
  RepairPad:        (1000, 5, 20, 50, 2, HeavyFactoryUpgrade),
  AircraftFactory:  (1150, 6, 60, 60, 3, Outpost),
  IxCenter:         (1000, 7, 40, 50, 5, (HeavyFactoryUpgrade, Outpost)),
  Starport:         (1500, 6, 60, 60, 6, Outpost),
  Palace:           (1600, 8, 65, 70, 6, IxResearchCenter),
  Wall:             (20,   1, 0,  30, 1),
  Silo:             (120,  2, 5,  20, 1, Refinery),
  GunTurret:        (550,  5, 15, 40, 5, Refinery),
  RocketTurret:     (750,  7, 25, 40, 7, (Outpost, ConstructionYardUpgrade))
}

requirements_upgrade = {
  # cost tech_level prerequisites house
  ConstructionYardUpgrade: (1000, 7, ConstructionYard),
  BarracksUpgrade:         (500,  3, Barracks),
  LightFactoryUpgrade:     (400,  3, LightFactory),
  HeavyFactoryUpgrade:     (800,  5, HeavyFactory),
  AircraftFactoryUpgrade:  (1500, 7, AircraftFactory, House.ATREIDES),
}

