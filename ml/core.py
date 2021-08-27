from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import EmailMessage

from background_task import background
from causalimpact import CausalImpact
import pandas as pd

from core.helpers import generate_random_number


@background(schedule=1)
def get_casual_impact_reports(uploaded_file_url, date):
    data = pd.read_csv(uploaded_file_url)
    data.dropna()

    data['Date'] = pd.Series(
        [datetime.strptime(str(df_date), '%m/%d/%Y').strftime('%Y-%m-%d') for df_date in data['Date']]
    )

    file_names = {
        0: 'only_clicks',
        1: 'x_impressions',
        2: 'x_ctr',
        3: 'x_position'
    }

    max_info = {
        'date': None,
        'X': None
    }

    max_result_y = None

    for delta in range(-7, 8):
        date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=delta)).strftime('%Y-%m-%d')

        pre_period = [data['Date'].iloc[0], date]
        post_period_date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        post_period = [post_period_date, data['Date'].iloc[-1]]

        data = pd.read_csv(f'/{uploaded_file_url}', index_col='Date')
        data.dropna()

        data['CTR'] = pd.Series([float(str(val).replace("%", "")) for val in data['CTR']], index=data.index)
        X_data = [[0]*len(data['Clicks']), data['Impressions'], data['CTR'], data['Position']]

        max_result_x = None
        max_info_x = None
        for index, X in enumerate(X_data):
            if index == 0:
                new_data = pd.DataFrame({'y': data['Clicks']})
            else:
                new_data = pd.DataFrame({'y': data['Clicks'], 'X': X})

            ci = CausalImpact(new_data, pre_period, post_period)

            if max_result_x is None:
                max_result_x = ci
                max_info_x = file_names[index]
            elif ci.p_value < max_result_x.p_value:
                max_result_x = ci
                max_info_x = file_names[index]

        if max_result_y is None:
            max_result_y = max_result_x
            max_info['X'] = max_info_x
            max_info['date'] = date
        elif max_result_y.p_value < max_result_x.p_value:
            max_result_y = max_result_x
            max_info['X'] = max_info_x
            max_info['date'] = date

    response = {}
    ci = max_result_y
    report = ci.summary() + '\n' + ci.summary(output='report')
    report_name = f'casual_report_{generate_random_number()}.txt'
    with open(f'{settings.REPORT_PATH}/{report_name}', 'w', encoding='utf-8') as file:
        file.write(report)

    figure_name = f'figure_{generate_random_number()}.png'
    figure_path = f'{settings.REPORT_PATH}/{figure_name}'
    ci.plot(savefig_path=figure_path)
    response[f'figure'] = f"{settings.REPORT_PATH}/{figure_name}"
    response[f'report'] = f"{settings.REPORT_PATH}/{report_name}"

    subject = 'Casual Impact Tool'
    message = f'Report is ready.\nDate: {max_info["date"]}\nCategory: {max_info["X"]}'

    from_email = settings.EMAIL_HOST_USER
    mail = EmailMessage(subject, message, from_email, ['abror.ruzibayev@gmail.com', 'k.kleinschmidt@searchmetrics.com'])
    for item in response:
        mail.attach_file(response[item])
    mail.send(fail_silently=False)
