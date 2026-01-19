import plotly.express as px
from scipy import stats
import pandas as pd
import numpy as np
import statsmodels.api as sm
from django.shortcuts import render, HttpResponse
from .models import CurrencyData    
def home(request):
    count = CurrencyData.objects.count()
    print(f"Записей в базе: {count}")
    return render(request, 'main/home.html')
def trends_view(request):
    all_currencies = CurrencyData.objects.values('letter_code', 'currency').distinct().order_by('letter_code')
    selected_currency = request.GET.get('currency', 'EUR')
    data = CurrencyData.objects.filter(letter_code=selected_currency).order_by('date')    
    if data.exists():
        df = pd.DataFrame(list(data.values('date', 'rate')))
        fig = px.line(df, x='date', y='rate', title=f'Динамика курса {selected_currency}',
                        labels={'date': 'время','rate': 'обменный курс (в рублях)'})
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#888')
            )
        chart_html = fig.to_html(full_html=False)
        rate = df['rate']
        max = rate.max()
        min = rate.min()
        mean = rate.mean()
        median = rate.median()
        mode = rate.mode().iloc[0]
        var = rate.var()
        std = rate.std()
        quantile_lower = rate.quantile(0.25)
        quantile_upper = rate.quantile(0.75)
        IQR = quantile_upper - quantile_lower
        Q1 = quantile_lower-IQR*1.5
        Q3 = quantile_upper+IQR*1.5
        s = {
            'Максимальное значение' : f'{max:.2f}',
            'Минимальное значение' : f'{min:.2f}',
            'Среднее': f'{mean:.2f}',
            'Медиана': f'{median:.2f}',
            'Мода': f'{mode:.2f}',
            'Дисперсия': f'{var:.2f}',
            'Станд. отклонение': f'{std:.2f}',
            'Нижний квартиль (Q1)': f'{quantile_lower:.2f}',
            'Верхний квартиль (Q3)': f'{quantile_upper:.2f}',
            'IQR (размах)': f'{IQR:.2f}',
            'Нижний выброс (Q1 - 1.5 * IQR)': f'{Q1:.2f}',
            'Верхний выброс (Q3 + 1.5 * IQR)': f'{Q3:.2f}',
        }
        stats_html = f"""
        <div class="mt-4 p-4 border rounded shadow-sm bg-body-tertiary">
            <h5 class="mb-4 text-primary">Сводная статистика: {selected_currency}</h5>
            <div class="row row-cols-1 row-cols-md-3 g-3">
        """
        for label, value in s.items():
            stats_html += f"""
                <div class="col">
                    <div class="p-2 border-bottom">
                        <small class="text-muted d-block">{label}</small>
                        <span class="fw-bold">{value}</span>
                    </div>
                </div>
            """
        chart_html = fig.to_html(full_html=False) + stats_html
    else:
        chart_html = "<p class='text-danger'>Данные для выбранной валюты не найдены</p>"
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return HttpResponse(chart_html)
    return render(request, 'main/trends.html', {
        'chart': chart_html,
        'currencies': all_currencies,
        'selected_currency': selected_currency
    })
def heatmap(request):
    all_currencies = CurrencyData.objects.values('letter_code', 'currency').distinct().order_by('letter_code')
    selected_codes = request.GET.getlist('currencies')
    mask = request.GET.get('mask')
    if not selected_codes:
        selected_codes = ['USD', 'EUR']
    data = CurrencyData.objects.filter(letter_code__in=selected_codes).values('date', 'letter_code', 'rate')
    if data.exists():
        df = pd.DataFrame(list(data))
        df_pivot = df.pivot_table(index='date', columns='letter_code', values='rate')
        df_pivot.fillna(method='ffill')
        corr_matrix = df_pivot.corr(method='spearman')        
        corr_matrix = corr_matrix.fillna(0)
        if mask == 'on':
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        corr_matrix[mask] = np.nan
        fig = px.imshow(
        corr_matrix, 
        text_auto=True, # Показывает цифры корреляции внутри квадратиков
        aspect="auto", 
        color_continuous_scale='blues',
        title="Тепловая карта корреляции валют",
        zmin=-1, zmax=1,        
        )
        fig.update_layout(xaxis_title="валюты", yaxis_title="валюты")
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#888')
            )
        chart_html = fig.to_html(full_html=False)        
    else:
        chart_html = "<p class='text-danger'>Выбранные данные не найдены</p>"
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return HttpResponse(chart_html) # Отдаем ТОЛЬКО график
    return render(request, 'main/heatmap.html', {
        'chart': chart_html,
        'currencies': all_currencies,
        'selected_currency': selected_codes,
        'mask': mask,
    })
from django.shortcuts import render
from .models import CurrencyData
import pandas as pd
import plotly.express as px
def regressions(request):
    all_currencies = CurrencyData.objects.values('letter_code', 'currency').distinct().order_by('letter_code')    
    curr_x = request.GET.get('curr_x', 'USD')
    curr_y = request.GET.get('curr_y', 'EUR')
    if curr_x == curr_y:
        chart_html = f"""
            <div class="alert alert-info mt-5 text-center">
                <h5>Выбраны 2 одинаковые валюты, поробуйте заново</h5>
            </div>
        """
    else:
        data = CurrencyData.objects.filter(letter_code__in=[curr_x, curr_y]).values('date', 'letter_code', 'rate')        
        if data.exists():
            df = pd.DataFrame(list(data))
            df_pivot = df.pivot_table(index='date', columns='letter_code', values='rate').dropna()            
            if not df_pivot.empty and curr_x in df_pivot.columns and curr_y in df_pivot.columns:
                try:
                    fig = px.scatter(
                        df_pivot, x=curr_x, y=curr_y, 
                        trendline="ols",
                        title=f"Регрессия: {curr_y} vs {curr_x}",
                        labels={curr_x: f"Курс {curr_x}", curr_y: f"Курс {curr_y}"},
                    )      
                    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
                    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
                    fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#888')
                    )
                    chart_html = fig.to_html(full_html=False)
                    X = df_pivot[curr_x]
                    y = df_pivot[curr_y]
                    X = sm.add_constant(X)
                    model = sm.OLS(y, X).fit()
                    summary_html = model.summary().as_html()
                    chart_html+=f"""
                        <div class="mt-4 p-3 border rounded shadow-sm bg-body-tertiary">
                            <h5 class="mb-3">Статистические показатели регрессии</h5>
                            <div class="table-responsive" style="font-size: 0.85rem;">
                                {summary_html}
                            </div>
                        </div>
                    """
                except Exception as e:
                    chart_html = f"<div class='alert alert-warning'>Ошибка расчета: {str(e)}</div>"
            else:
                chart_html = f"""
                    <div class="alert alert-warning mt-5 text-center">
                        <h5>Недостаточно общих данных</h5>
                        <p>Для валют {curr_x} и {curr_y} не найдено общих дат с заполненными курсами.</p>
                    </div>
                """
        else:
            chart_html = "<div class='alert alert-danger mt-5 text-center'>Данные в базе отсутствуют.</div>" 
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return HttpResponse(chart_html)
    return render(request, 'main/regressions.html', {
        'chart': chart_html,
        'currencies': all_currencies,
        'curr_x': curr_x,
        'curr_y': curr_y
    })