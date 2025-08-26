from django.shortcuts import render
import math

def index(request):
    result = None
    if request.method == 'POST':
        length = float(request.POST.get('length', 0))
        width = float(request.POST.get('width', 0))
        spacing_length_input = request.POST.get('spacing_length')
        spacing_width_input = request.POST.get('spacing_width')
        lag_spacing_input = request.POST.get('lag_spacing')
        beam_size = request.POST.get('beam_size', '6x6')
        floor_direction = request.POST.get('floor_direction', 'width')
        front_direction = request.POST.get('front_direction', floor_direction)

        beam_thickness = 0.2 if beam_size == '8x8' else 0.15
        front_board_thickness = 0.075
        post_diameter = 0.28
        extension = 0.2 if beam_size == '8x8' else 0.15
        max_post_spacing = 2.5
        deck_board_width = 0.15
        board_length = 6.0

        lag_spacing = float(lag_spacing_input) if lag_spacing_input else 0.30
        spacing_l_limit = float(spacing_length_input) if spacing_length_input else max_post_spacing
        spacing_w_limit = float(spacing_width_input) if spacing_width_input else max_post_spacing

        adjusted_length = length - (beam_thickness + front_board_thickness)
        adjusted_width = width

        count_l = 2
        while True:
            total_posts_width = count_l * post_diameter
            available_space = adjusted_length - total_posts_width
            if available_space < 0:
                break
            spacing_l = available_space / (count_l - 1)
            if spacing_l <= spacing_l_limit:
                break
            count_l += 1

        count_w = 2
        while True:
            total_posts_width = count_w * post_diameter
            available_space = adjusted_width - total_posts_width
            if available_space < 0:
                break
            spacing_w = available_space / (count_w - 1)
            if spacing_w <= spacing_w_limit:
                break
            count_w += 1

        total_posts = count_l * count_w

        if floor_direction == 'length':
            beam_run = adjusted_length + extension
            boards_per_row = 2 * count_w
            side_boards_total = beam_run * boards_per_row
            insert_pieces_total = spacing_l * (count_l - 1) * count_w
        else:
            beam_run = width
            boards_per_row = 2 * count_l
            side_boards_total = beam_run * boards_per_row
            insert_pieces_total = spacing_w * (count_w - 1) * count_l

        total_3x8_meters = round(side_boards_total + insert_pieces_total, 2)
        total_3x8_boards = math.ceil(total_3x8_meters / board_length)

        if floor_direction == 'length':
            num_lag_rows = math.ceil(adjusted_length / lag_spacing) + 1
            lag_row_length = width + 0.30
        else:
            num_lag_rows = math.ceil(width / lag_spacing) + 1
            lag_row_length = adjusted_length + 0.30

        total_lag_meterage = round(num_lag_rows * lag_row_length, 2)
        lag_boards_needed = math.ceil(total_lag_meterage / board_length)

        if floor_direction == 'length':
            board_rows = math.ceil(width / deck_board_width)
            board_run_length = adjusted_length
        else:
            board_rows = math.ceil(adjusted_length / deck_board_width)
            board_run_length = width

        total_deck_meterage = round(board_rows * board_run_length, 2)
        deck_boards_needed = math.ceil(total_deck_meterage / board_length)

        k_len = 3
        def num_boards_span(n, k):
            if n <= k:
                return 1
            return math.floor((n - k) / (k - 1)) + 1

        num_boards_length = num_boards_span(count_l, k_len)
        num_boards_width = num_boards_span(count_w, k_len)
        cross_count_length = 2 * num_boards_length * count_w
        cross_count_width = 2 * num_boards_width * count_l
        cross_count_total = cross_count_length + cross_count_width
        total_cross_meters = round(cross_count_total * board_length, 2)
        cross_boards_needed = cross_count_total

        bolts_total_length = (2 * count_l - 1) * count_w
        bolts_total_width = (2 * count_w - 1) * count_l
        total_bolts_cross = bolts_total_length + bolts_total_width

        row_length = adjusted_length if front_direction == 'length' else width
        posts_in_row = count_l if front_direction == 'length' else count_w
        num_front_rows = 3

        boards_per_front_row = math.ceil(row_length / board_length)
        connections_per_row = max(0, boards_per_front_row - 1)
        total_connections = connections_per_row * num_front_rows
        connection_length = total_connections * 1.20
        total_front_beam_meters = round(row_length * num_front_rows + connection_length, 2)
        total_front_beam_boards = boards_per_front_row * num_front_rows

        front_beam_bolts = posts_in_row * num_front_rows
        front_connection_bolts = total_connections * num_front_rows

        board_width_front = 0.075
        group_width = board_width_front * 4
        num_groups = math.ceil(row_length / group_width)
        front_boards_count = num_groups
        cubes_count = num_groups * 3
        front_board_length = 4.2
        front_boards_meters = round(front_boards_count * front_board_length, 2)
        front_board_screws = front_boards_count * 6
        cube_screws = cubes_count * 2

        lag_screws = lag_boards_needed * 4
        deck_screws = deck_boards_needed * (2 * num_lag_rows)

        total_beam_bolts = (count_l * count_w) + (count_l - 1) * count_w * 2
        total_bolt_count = (total_bolts_cross + total_beam_bolts + front_beam_bolts + front_connection_bolts)
        total_bolt_meterage = round(total_bolt_count * 0.50, 2)

        screws_40_count = front_board_screws
        screws_40_packs = math.ceil(screws_40_count / 25)
        screws_30_count = lag_screws + deck_screws + cube_screws

        total_3x6_boards = cross_boards_needed + lag_boards_needed + deck_boards_needed
        total_3x6_meterage = round(total_cross_meters + total_lag_meterage + total_deck_meterage, 2)

        total_area = round(length * width, 2)

        total_screws = (total_bolts_cross + total_beam_bolts + lag_screws + deck_screws +
                        front_beam_bolts + front_connection_bolts + front_board_screws + cube_screws)

        result = {
            'original_length': length,
            'original_width': width,
            'adjusted_length': round(adjusted_length, 3),
            'spacing_length': round(spacing_l, 3),
            'spacing_width': round(spacing_w, 3),
            'count_length': count_l,
            'count_width': count_w,
            'total_posts': total_posts,
            'beam_size': beam_size,
            'floor_direction': floor_direction,
            'front_direction': front_direction,
            'total_3x8_meters': total_3x8_meters,
            'total_3x8_boards': total_3x8_boards,
            'num_lag_rows': num_lag_rows,
            'lag_row_length': round(lag_row_length, 3),
            'total_lag_meterage': total_lag_meterage,
            'lag_boards_needed': lag_boards_needed,
            'board_rows': board_rows,
            'total_deck_meterage': total_deck_meterage,
            'deck_boards_needed': deck_boards_needed,
            'cross_count_total': cross_count_total,
            'total_cross_meters': total_cross_meters,
            'cross_boards_needed': cross_boards_needed,
            'total_bolts_cross': total_bolts_cross,
            'front_beam_meters': total_front_beam_meters,
            'front_beam_boards': total_front_beam_boards,
            'front_boards_count': front_boards_count,
            'front_boards_meters': front_boards_meters,
            'cubes_count': cubes_count,
            'front_board_screws': front_board_screws,
            'cube_screws': cube_screws,
            'lag_screws': lag_screws,
            'deck_screws': deck_screws,
            'total_3x6_boards': total_3x6_boards,
            'total_3x6_meterage': total_3x6_meterage,
            'total_bolt_count': total_bolt_count,
            'total_bolt_meterage': total_bolt_meterage,
            'screws_40_count': screws_40_count,
            'screws_40_packs': screws_40_packs,
            'screws_30_count': screws_30_count,
            'total_area': total_area,
            'total_screws': total_screws,
        }

        request.session['result_data'] = result

    return render(request, 'calculator/index.html', {'result': result})


def pricing(request):
    context = {}
    if request.method == 'POST':
        result_data = request.session.get('result_data')
        if not result_data:
            context['error'] = 'Сначала выполните расчёт материалов.'
            return render(request, 'calculator/pricing.html', context)

        price_3x8 = float(request.POST.get('price_3x8', 0))
        price_3x6 = float(request.POST.get('price_3x6', 0))
        price_6x6 = float(request.POST.get('price_6x6', 0))
        price_8x8 = float(request.POST.get('price_8x8', 0))
        price_bolt = float(request.POST.get('price_bolt', 0))
        price_screw_30 = float(request.POST.get('price_screw_30', 0))
        price_screw_40 = float(request.POST.get('price_screw_40', 0))
        price_day = float(request.POST.get('price_day', 0))
        days = int(request.POST.get('days', 0))

        cost_3x8 = result_data['total_3x8_meters'] * price_3x8
        total_3x6_meters_incl_front = (
            result_data['total_3x6_meterage'] + result_data['front_boards_meters'] + result_data['cubes_count'] * 0.075
        )
        cost_3x6 = total_3x6_meters_incl_front * price_3x6

        cost_6x6 = result_data['front_beam_meters'] * price_6x6 if result_data['beam_size'] == '6x6' else 0
        cost_8x8 = result_data['front_beam_meters'] * price_8x8 if result_data['beam_size'] == '8x8' else 0
        cost_bolts = result_data['total_bolt_meterage'] * price_bolt
        cost_screws_30 = result_data['screws_30_count'] * price_screw_30
        cost_screws_40 = result_data['screws_40_count'] * price_screw_40

        total_materials = cost_3x8 + cost_3x6 + cost_6x6 + cost_8x8 + cost_bolts + cost_screws_30 + cost_screws_40
        total_work = price_day * days
        total_price = total_materials + total_work

        context['result'] = {
            'cost_3x8': round(cost_3x8, 2),
            'cost_3x6': round(cost_3x6, 2),
            'cost_6x6': round(cost_6x6, 2),
            'cost_8x8': round(cost_8x8, 2),
            'cost_bolts': round(cost_bolts, 2),
            'cost_screws_30': round(cost_screws_30, 2),
            'cost_screws_40': round(cost_screws_40, 2),
            'total_materials': round(total_materials, 2),
            'days': days,
            'price_day': round(price_day, 2),
            'total_work': round(total_work, 2),
            'total_price': round(total_price, 2),
        }

    return render(request, 'calculator/pricing.html', context)