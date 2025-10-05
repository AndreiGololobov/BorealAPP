from django.shortcuts import render
import math
import json

def calculate_posts(length_for_spacing, width_for_spacing, spacing_length_limit, spacing_width_limit, post_diameter):
    """
    Расчёт стоек и их позиций для SVG-схемы.
    """
    count_l = 2
    spacing_l = 0.0
    if length_for_spacing > 0:
        while True:
            total_posts_width_l = count_l * post_diameter
            available_space_l = length_for_spacing - total_posts_width_l
            if available_space_l < 0:
                break
            spacing_l_candidate = available_space_l / (count_l - 1) if count_l > 1 else 0.0
            if spacing_l_candidate <= spacing_length_limit:
                spacing_l = spacing_l_candidate
                break
            count_l += 1

    count_w = 2
    spacing_w = 0.0
    if width_for_spacing > 0:
        while True:
            total_posts_width_w = count_w * post_diameter
            available_space_w = width_for_spacing - total_posts_width_w
            if available_space_w < 0:
                break
            spacing_w_candidate = available_space_w / (count_w - 1) if count_w > 1 else 0.0
            if spacing_w_candidate <= spacing_width_limit:
                spacing_w = spacing_w_candidate
                break
            count_w += 1

    total_posts = count_l * count_w
    positions = [{'x': round(i * spacing_l, 3), 'y': round(j * spacing_w, 3)} for i in range(count_l) for j in range(count_w)]
    return {
        'count_l': count_l,
        'count_w': count_w,
        'spacing_l': spacing_l,
        'spacing_w': spacing_w,
        'total_posts': total_posts,
        'positions': positions
    }

def index(request, lang='ru'):
    """
    Главная страница калькулятора с SVG-визуализацией.
    """
    # Language selection based on lang argument
    if lang == 'en':
        template_name = 'calculator/index_en.html'
    elif lang == 'no':
        template_name = 'calculator/index_no.html'
    else:
        template_name = 'calculator/index.html'

    if request.method == 'POST' and request.POST.get('action') == 'reset':
        request.session.flush()
        return render(request, template_name, {'result': None})

    result = request.session.get('result_data')

    if request.method == 'POST' and request.POST.get('action') != 'reset':
        try:
            length = float(request.POST.get('length', '0').replace(',', '.'))
            width = float(request.POST.get('width', '0').replace(',', '.'))
            if length <= 0 or width <= 0:
                raise ValueError("Размеры должны быть больше 0")
        except (TypeError, ValueError):
            return render(request, template_name, {'result': None, 'error': 'Введите корректные размеры'})

        spacing_length_input = request.POST.get('spacing_length')
        spacing_width_input = request.POST.get('spacing_width')
        lag_spacing_input = request.POST.get('lag_spacing')
        beam_size = request.POST.get('beam_size', '6x6')
        front_direction = request.POST.get('front_direction', 'length')
        deck_direction = request.POST.get('deck_direction', 'length')

        beam_thickness = 0.20 if beam_size == '8x8' else 0.15
        front_board_thickness = 0.075
        post_diameter = 0.28
        max_post_spacing = 2.5

        try:
            lag_spacing = float(lag_spacing_input.replace(',', '.')) if lag_spacing_input else 0.40
        except (TypeError, ValueError):
            lag_spacing = 0.40

        if front_direction == 'length':
            adjusted_length = length
            adjusted_width = width - (beam_thickness + front_board_thickness)
        else:
            adjusted_length = length - (beam_thickness + front_board_thickness)
            adjusted_width = width

        margin = 0.15
        length_for_spacing = adjusted_length if front_direction != 'length' else length - 2 * margin
        width_for_spacing = adjusted_width if front_direction == 'length' else width - 2 * margin

        try:
            spacing_length_limit = float(spacing_length_input.replace(',', '.')) if spacing_length_input else max_post_spacing
            spacing_width_limit = float(spacing_width_input.replace(',', '.')) if spacing_width_input else max_post_spacing
        except (TypeError, ValueError):
            spacing_length_limit = spacing_width_limit = max_post_spacing

        posts_data = calculate_posts(length_for_spacing, width_for_spacing, spacing_length_limit, spacing_width_limit, post_diameter)

        total_area = round(length * width, 3)
        result = {
            'original_length': round(length, 3),
            'original_width': round(width, 3),
            'adjusted_length': round(adjusted_length, 3),
            'adjusted_width': round(adjusted_width, 3),
            'spacing_length': round(posts_data['spacing_l'], 3),
            'spacing_width': round(posts_data['spacing_w'], 3),
            'count_length': posts_data['count_l'],
            'count_width': posts_data['count_w'],
            'total_posts': posts_data['total_posts'],
            'beam_size': beam_size,
            'front_direction': front_direction,
            'deck_direction': deck_direction,
            'total_area': total_area,
            'input_spacing_length': spacing_length_input or '',
            'input_spacing_width': spacing_width_input or '',
            'input_lag_spacing': lag_spacing_input or '',
            'schema_data': json.dumps({
                'dimensions': {'length': adjusted_length, 'width': adjusted_width},
                'posts': posts_data['positions'],
                'front_direction': front_direction,
                'deck_direction': deck_direction
            })
        }

        # Брусья 3×8
        board_length = 6.0
        release = 0.15 if beam_size == '6x6' else 0.20
        if deck_direction == 'length':
            line_length = adjusted_length + release
            num_rows = posts_data['count_w']
            total_lines = num_rows * 2
            inserts_total = (posts_data['count_l'] - 1) * posts_data['spacing_l'] * num_rows
        else:
            line_length = adjusted_width + release
            num_rows = posts_data['count_l']
            total_lines = num_rows * 2
            inserts_total = (posts_data['count_w'] - 1) * posts_data['spacing_w'] * num_rows

        total_3x8_main = line_length * total_lines
        total_3x8_meters = round(total_3x8_main + inserts_total, 2)
        total_3x8_boards = math.ceil(total_3x8_meters / board_length)

        bolts_through_posts = posts_data['count_l'] * posts_data['count_w']
        bolts_inserts = 2 * (posts_data['count_l'] - 1) * posts_data['count_w'] if deck_direction == 'length' else 2 * (posts_data['count_w'] - 1) * posts_data['count_l']
        total_bolts_beams = bolts_through_posts + bolts_inserts
        bolts_beam_meterage = round(total_bolts_beams * 0.5, 2)
        nuts_beam_count = total_bolts_beams * 2
        washers_beam_count = total_bolts_beams * 2

        result.update({
            'line_length_3x8': round(line_length, 3),
            'num_lines_3x8': total_lines,
            'inserts_3x8': round(inserts_total, 2),
            'total_3x8_meters': total_3x8_meters,
            'total_3x8_boards': total_3x8_boards,
            'bolts_beam_count': total_bolts_beams,
            'bolts_beam_meterage': bolts_beam_meterage,
            'nuts_beam_count': nuts_beam_count,
            'washers_beam_count': washers_beam_count,
        })

        # Лаги 3×6
        if deck_direction == 'length':
            num_lag_rows = math.ceil(adjusted_length / lag_spacing) + 1
            lag_row_length = adjusted_width + 0.30
            connection_rows = posts_data['count_w']
        else:
            num_lag_rows = math.ceil(adjusted_width / lag_spacing) + 1
            lag_row_length = adjusted_length + 0.30
            connection_rows = posts_data['count_l']
        total_lag_meterage = round(num_lag_rows * lag_row_length, 2)
        lag_boards_needed = math.ceil(total_lag_meterage / board_length)
        lag_screws = int(num_lag_rows * connection_rows * 2 * 3)

        result.update({
            'num_lag_rows': num_lag_rows,
            'lag_row_length': round(lag_row_length, 3),
            'total_lag_meterage': total_lag_meterage,
            'lag_boards_needed': lag_boards_needed,
            'lag_screws': lag_screws,
        })

        # Настил 3×6
        deck_board_width = 0.15
        if deck_direction == 'length':
            board_rows = math.ceil(adjusted_width / deck_board_width)
            board_run_length = adjusted_length
        else:
            board_rows = math.ceil(adjusted_length / deck_board_width)
            board_run_length = adjusted_width
        boards_per_row = math.ceil(board_run_length / board_length)
        deck_boards_needed = board_rows * boards_per_row
        total_deck_meterage = round(board_rows * board_run_length, 2)
        deck_screws = int(deck_boards_needed * num_lag_rows * 2)

        result.update({
            'board_rows': board_rows,
            'boards_per_row': boards_per_row,
            'total_deck_meterage': total_deck_meterage,
            'deck_boards_needed': deck_boards_needed,
            'deck_screws': deck_screws,
        })

        # Диагональные укосы 3×6
        diagonal_height = 3.0
        diag_board_length = 6.0

        def compute_diagonals_braces(n_posts, spacing, num_rows):
            n_gaps = max(n_posts - 1, 0)
            if n_gaps == 0 or spacing <= 0:
                return 0, 0.0, 0
            pairs = (n_gaps + 1) // 2
            length_per_row = 0.0
            for k in range(pairs):
                gaps_to_span = 1 if (k == pairs - 1 and n_gaps % 2 == 1) else 2
                diag_len = math.sqrt((gaps_to_span * spacing) ** 2 + diagonal_height ** 2)
                length_per_row += diag_len * 2
            braces_per_row = pairs * 2
            bolts_per_row = 3 * pairs + 2
            return braces_per_row * num_rows, length_per_row * num_rows, bolts_per_row * num_rows

        diag_count_len, diag_length_len, bolts_len = compute_diagonals_braces(posts_data['count_l'], posts_data['spacing_l'], posts_data['count_w'])
        diag_count_wid, diag_length_wid, bolts_wid = compute_diagonals_braces(posts_data['count_w'], posts_data['spacing_w'], posts_data['count_l'])
        total_diag_boards = diag_count_len + diag_count_wid
        total_diag_meters = diag_length_len + diag_length_wid
        total_bolts_cross = bolts_len + bolts_wid
        cross_boards_needed = math.ceil(total_diag_meters / diag_board_length) if diag_board_length > 0 else 0
        nuts_cross_count = total_bolts_cross * 2
        washers_cross_count = total_bolts_cross * 2

        result.update({
            'cross_count_length': diag_count_len,
            'cross_count_width': diag_count_wid,
            'cross_count_total': total_diag_boards,
            'total_cross_meters': round(total_diag_meters, 2),
            'cross_boards_needed': cross_boards_needed,
            'total_bolts_cross': total_bolts_cross,
            'nuts_cross_count': nuts_cross_count,
            'washers_cross_count': washers_cross_count,
        })

        # Фронт
        front_board_width = 0.15
        front_board_height = 4.20
        if front_direction == 'length':
            front_row_length = adjusted_length
            front_posts_in_row = posts_data['count_l']
        else:
            front_row_length = adjusted_width
            front_posts_in_row = posts_data['count_w']

        front_boards_count = 0
        front_boards_meters = 0.0
        front_cubes_count = 0
        front_board_screws = 0
        cube_screws = 0
        front_beam_meterage = 0.0
        front_beam_boards = 0
        front_connections = 0
        front_beam_bolts = 0
        front_beam_nuts = 0
        front_beam_washers = 0

        if front_row_length > 0 and front_posts_in_row > 0:
            module_width = front_board_width * 2
            modules_full = math.floor(front_row_length / module_width)
            front_boards_count = modules_full + 1
            front_boards_meters = front_boards_count * front_board_height
            front_cubes_count = (front_boards_count - 1) * 3
            front_board_screws = front_boards_count * 6
            cube_screws = front_cubes_count * 2

            num_front_rows = 3
            front_beam_row_length = front_row_length
            boards_per_front_row = math.ceil(front_beam_row_length / board_length)
            connections_per_row = max(boards_per_front_row - 1, 0)
            front_connections = connections_per_row * num_front_rows
            front_beam_meterage = front_beam_row_length * num_front_rows + front_connections * 1.20
            front_beam_boards = boards_per_front_row * num_front_rows
            bolts_for_posts = front_posts_in_row * num_front_rows
            bolts_for_connections = front_connections * 4
            front_beam_bolts = bolts_for_posts + bolts_for_connections
            front_beam_nuts = front_beam_bolts * 2
            front_beam_washers = front_beam_bolts * 2

        result.update({
            'front_boards_count': front_boards_count,
            'front_boards_meters': round(front_boards_meters, 2),
            'front_cubes_count': front_cubes_count,
            'front_board_screws': front_board_screws,
            'cube_screws': cube_screws,
            'front_beam_meterage': round(front_beam_meterage, 2),
            'front_beam_boards': front_beam_boards,
            'front_connections': front_connections,
            'front_beam_bolts': front_beam_bolts,
            'front_beam_nuts': front_beam_nuts,
            'front_beam_washers': front_beam_washers,
        })

        # Сводка
        total_3x8_meterage = total_3x8_meters
        total_3x8_board_count = total_3x8_boards
        total_3x6_meterage = (total_diag_meters + total_lag_meterage +
                              total_deck_meterage + front_boards_meters +
                              (front_cubes_count * 0.20))
        total_3x6_board_count = (cross_boards_needed + lag_boards_needed +
                                 deck_boards_needed + front_boards_count)
        total_guiding_meterage = front_beam_meterage
        total_guiding_board_count = front_beam_boards
        total_screws_30 = lag_screws + deck_screws + cube_screws
        total_screws_40 = front_board_screws
        total_bolt_count = total_bolts_beams + total_bolts_cross + front_beam_bolts
        total_bolt_meterage_effective = round(total_bolt_count * 0.50, 2)
        total_bolt_meterage_purchase = total_bolt_count
        total_nuts_count = nuts_beam_count + nuts_cross_count + front_beam_nuts
        total_washers_count = washers_beam_count + washers_cross_count + front_beam_washers

        result.update({
            'total_posts_count': posts_data['total_posts'],
            'total_3x8_meterage': round(total_3x8_meterage, 2),
            'total_3x8_board_count': total_3x8_board_count,
            'total_3x6_meterage': round(total_3x6_meterage, 2),
            'total_3x6_board_count': total_3x6_board_count,
            'total_guiding_meterage': round(total_guiding_meterage, 2),
            'total_guiding_board_count': total_guiding_board_count,
            'total_screws_30': total_screws_30,
            'total_screws_40': total_screws_40,
            'total_bolt_count': total_bolt_count,
            'total_bolt_meterage_effective': total_bolt_meterage_effective,
            'total_bolt_meterage_purchase': total_bolt_meterage_purchase,
            'total_nuts_count': total_nuts_count,
            'total_washers_count': total_washers_count,
        })

        request.session['result_data'] = result

    return render(request, template_name, {'result': result})

def pricing(request, lang='ru'):
    """
    Страница расчёта стоимости с графиком.
    """
    # Language selection based on lang argument
    if lang == 'en':
        template_name = 'calculator/pricing_en.html'
    elif lang == 'no':
        template_name = 'calculator/pricing_no.html'
    else:
        template_name = 'calculator/pricing.html'

    if request.method == 'POST' and request.POST.get('action') == 'reset':
        request.session.flush()
        return render(request, template_name, {'result': None, 'pricing_inputs': {}})

    context = {}
    result_data = request.session.get('result_data')
    context['materials'] = result_data
    pricing_result = request.session.get('pricing_result', {})
    pricing_inputs = request.session.get('pricing_inputs', {
        'price_3x8': 0, 'price_3x6': 0, 'price_6x6': 0, 'price_8x8': 0,
        'price_bolt': 0, 'price_screw_30': 0, 'price_screw_40': 0,
        'price_post': 0, 'price_nut': 0, 'price_washer': 0,
        'price_day': 0, 'days': 0,
    })

    context['pricing_inputs'] = pricing_inputs

    if request.method == 'POST' and request.POST.get('action') != 'reset':
        if not result_data:
            context['error'] = 'Сначала выполните расчёт материалов.'
            return render(request, template_name, context)

        try:
            pricing_inputs = {
                'price_3x8': float(str(request.POST.get('price_3x8', 0)).replace(',', '.')),
                'price_3x6': float(str(request.POST.get('price_3x6', 0)).replace(',', '.')),
                'price_6x6': float(str(request.POST.get('price_6x6', 0)).replace(',', '.')),
                'price_8x8': float(str(request.POST.get('price_8x8', 0)).replace(',', '.')),
                'price_bolt': float(str(request.POST.get('price_bolt', 0)).replace(',', '.')),
                'price_screw_30': float(str(request.POST.get('price_screw_30', 0)).replace(',', '.')),
                'price_screw_40': float(str(request.POST.get('price_screw_40', 0)).replace(',', '.')),
                'price_post': float(str(request.POST.get('price_post', 0)).replace(',', '.')),
                'price_nut': float(str(request.POST.get('price_nut', 0)).replace(',', '.')),
                'price_washer': float(str(request.POST.get('price_washer', 0)).replace(',', '.')),
                'price_day': float(str(request.POST.get('price_day', 0)).replace(',', '.')),
                'days': int(float(str(request.POST.get('days', 0)).replace(',', '.'))),
            }
        except (ValueError, TypeError):
            context['error'] = 'Введите корректные числовые значения для цен.'
            return render(request, template_name, context)

        request.session['pricing_inputs'] = pricing_inputs

        cost_3x8 = result_data.get('total_3x8_meterage', 0) * pricing_inputs['price_3x8']
        cost_3x6 = result_data.get('total_3x6_meterage', 0) * pricing_inputs['price_3x6']
        cost_6x6 = result_data.get('total_guiding_meterage', 0) * pricing_inputs['price_6x6'] if result_data.get('beam_size') == '6x6' else 0
        cost_8x8 = result_data.get('total_guiding_meterage', 0) * pricing_inputs['price_8x8'] if result_data.get('beam_size') == '8x8' else 0
        cost_bolts = result_data.get('total_bolt_meterage_purchase', 0) * pricing_inputs['price_bolt']
        cost_screws30 = result_data.get('total_screws_30', 0) * pricing_inputs['price_screw_30']
        cost_screws40 = result_data.get('total_screws_40', 0) * pricing_inputs['price_screw_40']
        cost_posts = result_data.get('total_posts_count', 0) * pricing_inputs['price_post']
        cost_nuts = result_data.get('total_nuts_count', 0) * pricing_inputs['price_nut']
        cost_washers = result_data.get('total_washers_count', 0) * pricing_inputs['price_washer']

        total_materials = (cost_3x8 + cost_3x6 + cost_6x6 + cost_8x8 +
                           cost_bolts + cost_screws30 + cost_screws40 +
                           cost_posts + cost_nuts + cost_washers)
        total_work = pricing_inputs['price_day'] * pricing_inputs['days']
        total_price = total_materials + total_work

        pricing_result = {
            'cost_3x8': round(cost_3x8, 2),
            'cost_3x6': round(cost_3x6, 2),
            'cost_6x6': round(cost_6x6, 2),
            'cost_8x8': round(cost_8x8, 2),
            'cost_bolts': round(cost_bolts, 2),
            'cost_screws_30': round(cost_screws30, 2),
            'cost_screws_40': round(cost_screws40, 2),
            'cost_posts': round(cost_posts, 2),
            'cost_nuts': round(cost_nuts, 2),
            'cost_washers': round(cost_washers, 2),
            'total_materials': round(total_materials, 2),
            'days': pricing_inputs['days'],
            'price_day': round(pricing_inputs['price_day'], 2),
            'total_work': round(total_work, 2),
            'total_price': round(total_price, 2),
        }
        request.session['pricing_result'] = pricing_result

        # Проверка: сохранить PDF
        if request.POST.get('action') == 'download_pdf':
            from django.http import HttpResponse
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors

            include_details = request.POST.get('include_details') == '1'

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="offer.pdf"'

            doc = SimpleDocTemplate(response)
            styles = getSampleStyleSheet()
            elements = []

            # Header
            # Select language for PDF header
            if lang == 'en':
                elements.append(Paragraph("Quotation", styles['Title']))
                elements.append(Paragraph("Boreal Maritim AS", styles['Normal']))
                elements.append(Paragraph("Org.nr: 912 345 678", styles['Normal']))
                elements.append(Paragraph("Hamneveien 14, 9180 Skjervøy, Norway", styles['Normal']))
                elements.append(Paragraph("E-mail: post@borealmaritim.no", styles['Normal']))
                elements.append(Paragraph("Phone: +47 123 45 678", styles['Normal']))
                elements.append(Paragraph("<br/><br/>", styles['Normal']))
            elif lang == 'no':
                elements.append(Paragraph("Tilbud", styles['Title']))
                elements.append(Paragraph("Boreal Maritim AS", styles['Normal']))
                elements.append(Paragraph("Org.nr: 912 345 678", styles['Normal']))
                elements.append(Paragraph("Hamneveien 14, 9180 Skjervøy, Norge", styles['Normal']))
                elements.append(Paragraph("E-post: post@borealmaritim.no", styles['Normal']))
                elements.append(Paragraph("Telefon: +47 123 45 678", styles['Normal']))
                elements.append(Paragraph("<br/><br/>", styles['Normal']))
            else:
                elements.append(Paragraph("Смета", styles['Title']))
                elements.append(Paragraph("Boreal Maritim AS", styles['Normal']))
                elements.append(Paragraph("Орг.№: 912 345 678", styles['Normal']))
                elements.append(Paragraph("Hamneveien 14, 9180 Skjervøy, Норвегия", styles['Normal']))
                elements.append(Paragraph("E-mail: post@borealmaritim.no", styles['Normal']))
                elements.append(Paragraph("Телефон: +47 123 45 678", styles['Normal']))
                elements.append(Paragraph("<br/><br/>", styles['Normal']))

            # Materials table, if checkbox is selected
            if include_details and result_data:
                if lang == 'en':
                    data = [["Material", "Length (m)", "Quantity (pcs)", "Price (NOK)", "Total (NOK)"]]
                elif lang == 'no':
                    data = [["Materiale", "Lengde (m)", "Antall (stk)", "Pris (NOK)", "Sum (NOK)"]]
                else:
                    data = [["Материал", "Длина (м)", "Количество (шт)", "Цена (NOK)", "Сумма (NOK)"]]
                data.append(["Beams 3×8", result_data.get('total_3x8_meterage', 0), result_data.get('total_3x8_board_count', 0), pricing_inputs.get('price_3x8', 0), pricing_result.get('cost_3x8', 0)])
                data.append(["Material 3×6", result_data.get('total_3x6_meterage', 0), result_data.get('total_3x6_board_count', 0), pricing_inputs.get('price_3x6', 0), pricing_result.get('cost_3x6', 0)])
                data.append([f"{result_data.get('beam_size')} guiding", result_data.get('total_guiding_meterage', 0), result_data.get('total_guiding_board_count', 0), pricing_inputs.get(f"price_{result_data.get('beam_size')}", 0), pricing_result.get(f"cost_{result_data.get('beam_size')}", 0)])
                data.append(["Posts", "-", result_data.get('total_posts_count', 0), pricing_inputs.get('price_post', 0), pricing_result.get('cost_posts', 0)])
                data.append(["Screws 30 mm", "-", result_data.get('total_screws_30', 0), pricing_inputs.get('price_screw_30', 0), pricing_result.get('cost_screws_30', 0)])
                data.append(["Screws 40 mm", "-", result_data.get('total_screws_40', 0), pricing_inputs.get('price_screw_40', 0), pricing_result.get('cost_screws_40', 0)])
                data.append(["Bolts", result_data.get('total_bolt_meterage_purchase', 0), result_data.get('total_bolt_count', 0), pricing_inputs.get('price_bolt', 0), pricing_result.get('cost_bolts', 0)])
                data.append(["Nuts", "-", result_data.get('total_nuts_count', 0), pricing_inputs.get('price_nut', 0), pricing_result.get('cost_nuts', 0)])
                data.append(["Washers", "-", result_data.get('total_washers_count', 0), pricing_inputs.get('price_washer', 0), pricing_result.get('cost_washers', 0)])

                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.grey),
                    ('GRID', (0,0), (-1,-1), 1, colors.black),
                ]))
                elements.append(table)

            # Totals
            if lang == 'en':
                elements.append(Paragraph(f"<b>Total materials: {pricing_result.get('total_materials', 0)} NOK</b>", styles['Normal']))
                elements.append(Paragraph(f"Work: {pricing_result.get('total_work', 0)} NOK", styles['Normal']))
                elements.append(Paragraph(f"<b>Grand total: {pricing_result.get('total_price', 0)} NOK</b>", styles['Title']))
            elif lang == 'no':
                elements.append(Paragraph(f"<b>Totale materialer: {pricing_result.get('total_materials', 0)} NOK</b>", styles['Normal']))
                elements.append(Paragraph(f"Arbeid: {pricing_result.get('total_work', 0)} NOK", styles['Normal']))
                elements.append(Paragraph(f"<b>Totalsum: {pricing_result.get('total_price', 0)} NOK</b>", styles['Title']))
            else:
                elements.append(Paragraph(f"<b>Всего материалы: {pricing_result.get('total_materials', 0)} NOK</b>", styles['Normal']))
                elements.append(Paragraph(f"Работы: {pricing_result.get('total_work', 0)} NOK", styles['Normal']))
                elements.append(Paragraph(f"<b>Итого: {pricing_result.get('total_price', 0)} NOK</b>", styles['Title']))

            doc.build(elements)
            return response

    context['result'] = pricing_result
    return render(request, template_name, context)


# --- Language-specific views ---

def index_en(request):
    """English version of index page"""
    return index(request, lang='en')

def pricing_en(request):
    """English version of pricing page"""
    return pricing(request, lang='en')

def index_no(request):
    """Norwegian version of index page"""
    return index(request, lang='no')

def pricing_no(request):
    """Norwegian version of pricing page"""
    return pricing(request, lang='no')