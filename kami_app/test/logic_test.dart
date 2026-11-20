import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:kami_app/data/models/product.dart';
import 'package:kami_app/data/repositories/shop_repository.dart';
import 'package:kami_app/features/cart/cart_controller.dart';
import 'package:kami_app/features/quiz/quiz_logic.dart';
import 'package:kami_app/features/routine/reminder.dart';
import 'package:kami_app/features/routine/reminder_templates.dart';
import 'package:material_ui/material_ui.dart';

Catalog _snapshot() {
  final data = jsonDecode(File('assets/data/products.json').readAsStringSync()) as Map<String, dynamic>;
  return Catalog(
    products: [for (final p in data['products'] as List) Product.fromSnapshot(p as Map<String, dynamic>)],
    collections: (data['collections'] as Map<String, dynamic>).map(
      (k, v) => MapEntry(k, (v as List).cast<String>()),
    ),
  );
}

void main() {
  group('snapshot catalog', () {
    final c = _snapshot();

    test('has all bestsellers and categories', () {
      expect(c.bestsellers, hasLength(6));
      for (final key in ['neurodermitis', 'psoriasis', 'narbenpflege', 'anti-aging-pflege']) {
        expect(c.inCollection(key), isNotEmpty, reason: key);
      }
    });

    test('sale prices and discount', () {
      final set = c.byHandle('kami-neurodermitis-starter-set-1')!;
      expect(set.price, 86);
      expect(set.compareAtPrice, 102);
      expect(set.discountPercent, 16);
      expect(c.offers.first.discountPercent, greaterThanOrEqualTo(set.discountPercent));
    });

    test('single products carry usage and ingredients', () {
      final oil = c.byHandle(P.oil)!;
      expect(oil.usage, contains('Pipette'));
      expect(oil.ingredients, contains('Marmot oil'));
    });

    test('every quiz product exists in the shop', () {
      for (final h in [
        P.oil,
        P.rollOn,
        P.balm,
        P.spray,
        P.wash,
        P.neuroSet,
        P.psoriasisSet,
        P.scarSet,
        P.homeGoSet,
      ]) {
        expect(c.byHandle(h), isNotNull, reason: h);
      }
    });
  });

  group('quiz', () {
    test('neurodermitis + acute recommends oil or the neuro set', () {
      final r = evaluateQuiz({
        'who': 'me',
        'concern': 'neuro',
        'state': 'acute',
        'texture': 'oil',
        'where': 'small',
      });
      expect([P.oil, P.neuroSet], contains(r.primary));
      expect(r.reasons.first, contains('SOS Hautpflegeöl'));
    });

    test('scalp recommends the 2-phase spray', () {
      final r = evaluateQuiz({
        'who': 'me',
        'concern': 'scalp',
        'state': 'calm',
        'texture': 'any',
        'where': 'body',
      });
      expect(r.primary, P.spray);
    });

    test('dislike of oil prefers balm', () {
      final r = evaluateQuiz({
        'who': 'me',
        'concern': 'dry',
        'state': 'scaly',
        'texture': 'balm',
        'where': 'small',
      });
      expect(r.primary, P.balm);
    });

    test('babies never get a product recommendation', () {
      final r = evaluateQuiz({'who': 'baby'});
      expect(r.blocked, isTrue);
      expect(r.primary, isNull);
      expect(r.alsoGood, isEmpty);
    });
  });

  group('reminders', () {
    final start = DateTime(2026, 11, 2); // Monday
    final r = Reminder(
      id: '1',
      title: 'Öl',
      body: '',
      times: const [TimeOfDay(hour: 20, minute: 0), TimeOfDay(hour: 8, minute: 0)],
      startDate: start,
      cycle: true,
    );

    test('3 weeks on, 1 week off', () {
      expect(r.isActiveOn(start), isTrue);
      expect(r.isActiveOn(start.add(const Duration(days: 20))), isTrue);
      expect(r.isActiveOn(start.add(const Duration(days: 21))), isFalse);
      expect(r.isActiveOn(start.add(const Duration(days: 27))), isFalse);
      expect(r.isActiveOn(start.add(const Duration(days: 28))), isTrue);
      expect(r.isActiveOn(start.subtract(const Duration(days: 1))), isFalse);
    });

    test('weekday filter and disabled state', () {
      final weekend = r.copyWith(cycle: false, weekdays: {6, 7});
      expect(weekend.isActiveOn(start), isFalse); // Monday
      expect(weekend.isActiveOn(DateTime(2026, 11, 7)), isTrue); // Saturday
      expect(r.copyWith(enabled: false).isActiveOn(start), isFalse);
    });

    test('times are sorted and survive JSON', () {
      expect(r.sortedTimes.map(formatTime), ['08:00', '20:00']);
      final copy = Reminder.fromJson(jsonDecode(jsonEncode(r.toJson())) as Map<String, dynamic>);
      expect(copy.cycle, isTrue);
      expect(copy.times.map(formatTime).toSet(), {'08:00', '20:00'});
      expect(copy.startDate, start);
    });

    test('sets map to the oil template', () {
      expect(reminderTemplateFor('psoriasis-set')?.key, 'oil');
      expect(reminderTemplateFor(P.spray)?.key, 'spray');
      expect(reminderTemplateFor('kami-skincare-shopper'), isNull);
    });
  });

  group('cart', () {
    final c = _snapshot();
    final balm = c.byHandle(P.balm)!;
    final set = c.byHandle(P.neuroSet)!;
    final cart = CartState([
      CartLine(product: balm, variant: balm.defaultVariant, quantity: 1),
      CartLine(product: set, variant: set.defaultVariant, quantity: 2),
    ]);

    test('totals, savings and free shipping', () {
      expect(cart.count, 3);
      expect(cart.subtotal, 48 + 2 * 86);
      expect(cart.savings, 2 * (102 - 86));
      expect(cart.missingForFreeShipping, 0);
      final small = CartState([CartLine(product: balm, variant: balm.defaultVariant, quantity: 1)]);
      expect(small.missingForFreeShipping, 12);
    });

    test('checkout permalink', () {
      final uri = cart.checkoutUri(discountCode: 'KAMI10');
      expect(uri.host, 'www.kami-skincare.com');
      expect(uri.path, '/cart/${balm.defaultVariant.id}:1,${set.defaultVariant.id}:2');
      expect(uri.queryParameters['discount'], 'KAMI10');
    });
  });
}
