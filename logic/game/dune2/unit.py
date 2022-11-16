import logic.field

characteristics = {
  # cost tech_level armor speed attack_radius recon_radius prerequisites house
  LightInfantry: (50,   2, 5,   3,  2, 2, Barracks),
  Trooper:       (90,   3, 7,   3,  2, 2, BarracksUpgrade),
  Engineer:      (400,  4, 5,   3,  0, 2, BarracksUpgrade),
  Sardaukar:     (200,  7, 12,  5,  3, 3, BarracksUpgrade, House.IMPERATOR),
  Fremen:        (None, 8, 10,  5,  3, 5, Palace, House.ATREIDES),
  Trike:         (300,  2, 40,  10, 2, 3, LightFactoryUpgrade),
  Quad:          (400,  3, 50,  8,  3, 4, LightFactoryUpgrade),
  MCV:           (2000, 4, 40,  4,  0, 2, HeavyFactoryUpgrade),
  CombatTank:    (700,  4, 100, 6,  4, 4, HeavyFactory),
  SiegeTank:     (700,  6, 80,  5,  5, 5, HeavyFactoryUpgrade),
  Launcher:      (900,  5, 50,  5,  8, 5, HeavyFactoryUpgrade, House.ALL & ~House.ORDOS),
  SonicTank:     (1000, 7, 70,  5,  7, 6, (HeavyFactoryUpgrade, IxCenter), House.ATREIDES),
  Devastator:    (1050, 7, 130, 3,  4, 5, (HeavyFactoryUpgrade, IxCenter), House.HARKONNEN),
  Deviator:      (1000, 7, 50,  5,  8, 5, (HeavyFactoryUpgrade, IxCenter), House.ORDOS),
  Harvester:     (1200, 4, 100, 4,  0, 4, HeavyFactory),
  Carryall:      (1100, 6, 100, 10, 0, 5, AircraftFactory)
}

# Туман войны
# После каждого перемещения юнита / строительства здания смотрим, нужно ли отобразить это противнику (рисуем на его слое юнитов)
# Как происходит строительство / передвижение? Есть набор фабрик и юнитов, некоторые настроены на автоматическую работу (разные стратегии), некоторые нет
# Начался ход. Можно построить одно здание/юнит на фабрику и передвинуть либо атаковать юнитами

# Возможность походить часть хода и сделать несколько мувов юнитом за ход
# Электричество

# Атака
# Броня и починка зданий
# Стрельба поверх заборов и нет
# Продажа зданий
# Аутпост, помимо прочего, повышает радиус разведки

# Турреты
# Орнитоптер
# Рука смерти
# Видимость юнитов
# Фримены
# Червь

# Запланированное строительство юнитов / зданий
# Автоматическая починка
# Автоматическая работа харвестеров
# Автоматический относ харвестеров
# Автоматическое движение юнитов
# Здание прорисовывается, даже если в данный момент его не видно

class Unit:
  def __init__(self, armor, speed, attack_radius, recon_radius, house, field):
    self.health = armor
    self.speed = speed
    self.attack_radius = attack_radius
    self.recon_radius = recon_radius
    self.house = house
    self.field = field

  def move(self, from_cell, to_cell):
    if len(shortest_free_path(self.field, from_cell, to_cell)) > self.speed - 1:
      return False

    logic.field.kill_if_placed(self.field, from_cell.coords, to_cell.coords)
    return True

  def attack(self, cell):
    pass

class Infantry(Unit):
  def move(self, from_cell, to_cell):
    return not to_cell.unit and Unit.move(self, from_cell, to_cell)

class Vehicle(Unit):
  def move(self, from_cell, to_cell):
    return to_cell.terrain != Terrain.MOUNTAIN and \
           not to_cell.unit and \
           Unit.move(self, from_cell, to_cell)

class Tank(Unit):
  def move(self, from_cell, to_cell):
    return to_cell.terrain != Terrain.MOUNTAIN and \
           (not to_cell.unit or \
            isinstance(to_cell.unit, Infantry) and are_allies(self, to_cell.unit)) and \
           Unit.move(self, from_cell, to_cell)

class Aircraft(Unit):
  def move(self, from_cell, to_cell):
    return not to_cell.unit and Unit.move(self, from_cell, to_cell)

class Harvester(Tank):
  def __init__(self, armor, speed, radius, house, field):
    Tank.__init__(self, armor, speed, radius, house, field)
    self.spice_amount = 0
    self.max_spice_amount = 700

  def move(self, from_cell, to_cell):
    self.spice_amount = min(to_cell.spice_amount, self.max_spice_amount)
    to_cell.spice_amount = 0
    return Tank.move(self, from_cell, to_cell)

def are_allies(unit1, unit2):
  return unit1 and unit2 and unit1.house != unit2.house

