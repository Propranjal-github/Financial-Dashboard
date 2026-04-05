from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render

from accounts.serializers import UserManagementSerializer
from records.models import FinancialRecord
from records.serializers import FinancialRecordSerializer

User = get_user_model()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def login_view(request):
    """Login page. Authenticates via Django session auth."""
    if request.user.is_authenticated:
        return redirect('frontend:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not user.is_active:
                return render(request, 'login.html', {
                    'error': 'This account has been deactivated.',
                    'username': username,
                })
            login(request, user)
            return redirect('frontend:dashboard')
        return render(request, 'login.html', {
            'error': 'Invalid username or password.',
            'username': username,
        })

    return render(request, 'login.html')


def logout_view(request):
    """Log out and redirect to login page."""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('frontend:login')


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required(login_url='/login/')
def dashboard_view(request):
    """Dashboard with summary and analytics (role-aware)."""
    qs = FinancialRecord.objects.all()

    # Summary (all users)
    totals = qs.aggregate(
        total_income=Sum('amount', filter=Q(record_type='income')),
        total_expense=Sum('amount', filter=Q(record_type='expense')),
        record_count=Count('id'),
    )
    total_income = totals['total_income'] or 0
    total_expense = totals['total_expense'] or 0

    summary = {
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': total_income - total_expense,
        'record_count': totals['record_count'],
    }

    recent_records = qs.order_by('-created_at')[:5]

    context = {'summary': summary, 'recent_records': recent_records}

    # Analytics (analyst + admin only)
    if request.user.role in ('analyst', 'admin'):
        context['category_breakdown'] = list(
            qs.values('category').annotate(
                total=Sum('amount'), count=Count('id'),
            ).order_by('-total')
        )
        context['monthly_trends'] = list(
            qs.annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(
                income=Sum('amount', filter=Q(record_type='income')),
                expense=Sum('amount', filter=Q(record_type='expense')),
            )
            .order_by('month')
        )
        for entry in context['monthly_trends']:
            entry['month'] = entry['month'].strftime('%Y-%m') if entry['month'] else None
            entry['income'] = entry['income'] or 0
            entry['expense'] = entry['expense'] or 0

    return render(request, 'dashboard.html', context)


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@login_required(login_url='/login/')
def records_view(request):
    """List financial records with filtering and pagination."""
    qs = FinancialRecord.objects.select_related('created_by').all()

    # Collect filters
    filters = {}
    for key in ('record_type', 'category', 'status', 'date_from', 'date_to'):
        val = request.GET.get(key, '').strip()
        if val:
            filters[key] = val

    # Apply filters
    if 'record_type' in filters:
        qs = qs.filter(record_type=filters['record_type'])
    if 'category' in filters:
        qs = qs.filter(category__icontains=filters['category'])
    if 'status' in filters:
        qs = qs.filter(status=filters['status'])
    if 'date_from' in filters:
        qs = qs.filter(date__gte=filters['date_from'])
    if 'date_to' in filters:
        qs = qs.filter(date__lte=filters['date_to'])

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'records.html', {
        'records': page_obj,
        'page_obj': page_obj,
        'filters': filters,
    })


@login_required(login_url='/login/')
def record_create_view(request):
    """Create a financial record (admin only)."""
    if request.user.role != 'admin':
        messages.error(request, 'You do not have permission to create records.')
        return redirect('frontend:records')

    if request.method == 'POST':
        data = {
            'amount': request.POST.get('amount', ''),
            'record_type': request.POST.get('record_type', ''),
            'category': request.POST.get('category', ''),
            'date': request.POST.get('date', ''),
            'description': request.POST.get('description', ''),
            'status': request.POST.get('status', 'pending'),
        }
        serializer = FinancialRecordSerializer(data=data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            messages.success(request, 'Record created successfully.')
            return redirect('frontend:records')
        return render(request, 'record_create.html', {
            'errors': serializer.errors,
            'form_data': data,
        })

    return render(request, 'record_create.html')


# ---------------------------------------------------------------------------
# User Management (Admin only)
# ---------------------------------------------------------------------------

@login_required(login_url='/login/')
def users_view(request):
    """List all users (admin only)."""
    if request.user.role != 'admin':
        messages.error(request, 'You do not have permission to manage users.')
        return redirect('frontend:dashboard')

    users = User.objects.all().order_by('id')
    return render(request, 'users.html', {'users': users})


@login_required(login_url='/login/')
def user_create_view(request):
    """Create a new user (admin only)."""
    if request.user.role != 'admin':
        messages.error(request, 'You do not have permission to create users.')
        return redirect('frontend:dashboard')

    if request.method == 'POST':
        data = {
            'username': request.POST.get('username', ''),
            'email': request.POST.get('email', ''),
            'password': request.POST.get('password', ''),
            'role': request.POST.get('role', 'viewer'),
        }
        serializer = UserManagementSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, f'User "{data["username"]}" created successfully.')
            return redirect('frontend:users')
        return render(request, 'user_create.html', {
            'errors': serializer.errors,
            'form_data': data,
        })

    return render(request, 'user_create.html')


@login_required(login_url='/login/')
def user_delete_view(request, pk):
    """Delete a user (admin only, POST only)."""
    if request.user.role != 'admin':
        messages.error(request, 'You do not have permission to delete users.')
        return redirect('frontend:dashboard')

    if request.method == 'POST':
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('frontend:users')

        if user.pk == request.user.pk:
            messages.error(request, 'You cannot delete yourself.')
            return redirect('frontend:users')

        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" has been deleted.')

    return redirect('frontend:users')


# ---------------------------------------------------------------------------
# Analytics (Analyst + Admin only)
# ---------------------------------------------------------------------------

@login_required(login_url='/login/')
def analytics_view(request):
    """Financial analysis: daily / monthly / yearly / custom range."""
    if request.user.role not in ('analyst', 'admin'):
        messages.error(request, 'You do not have permission to access analytics.')
        return redirect('frontend:dashboard')

    analysis_type = request.GET.get('type', '')
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    params = dict(request.GET.items())

    context = {'mode': analysis_type or 'daily', 'params': params}

    # Only run analysis if the form was submitted
    if not analysis_type and not (start_date and end_date):
        return render(request, 'analytics.html', context)

    qs = FinancialRecord.objects.all()
    label = ''
    include_daily_trend = False
    include_monthly_trend = False

    # Custom range
    if start_date and end_date:
        try:
            s = datetime.strptime(start_date, '%Y-%m-%d').date()
            e = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            context['error'] = 'Invalid date format. Use YYYY-MM-DD.'
            return render(request, 'analytics.html', context)
        if s > e:
            context['error'] = 'Start date must be before end date.'
            return render(request, 'analytics.html', context)
        qs = qs.filter(date__gte=s, date__lte=e)
        label = f'{start_date} to {end_date}'
        context['mode'] = 'custom'
        include_daily_trend = True

    elif analysis_type == 'daily':
        date_str = request.GET.get('date', '').strip()
        if not date_str:
            context['error'] = 'Date is required for daily analysis.'
            return render(request, 'analytics.html', context)
        try:
            d = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            context['error'] = 'Invalid date format. Use YYYY-MM-DD.'
            return render(request, 'analytics.html', context)
        qs = qs.filter(date=d)
        label = date_str

    elif analysis_type == 'monthly':
        month_str = request.GET.get('month', '').strip()
        if not month_str:
            context['error'] = 'Month is required for monthly analysis.'
            return render(request, 'analytics.html', context)
        try:
            dt = datetime.strptime(month_str, '%Y-%m')
        except ValueError:
            context['error'] = 'Invalid month format. Use YYYY-MM.'
            return render(request, 'analytics.html', context)
        qs = qs.filter(date__year=dt.year, date__month=dt.month)
        label = month_str
        include_daily_trend = True

    elif analysis_type == 'yearly':
        year_str = request.GET.get('year', '').strip()
        if not year_str:
            context['error'] = 'Year is required for yearly analysis.'
            return render(request, 'analytics.html', context)
        try:
            year = int(year_str)
        except ValueError:
            context['error'] = 'Invalid year format.'
            return render(request, 'analytics.html', context)
        qs = qs.filter(date__year=year)
        label = year_str
        include_monthly_trend = True

    else:
        context['error'] = 'Invalid analysis type.'
        return render(request, 'analytics.html', context)

    # Build analysis data
    totals = qs.aggregate(
        total_income=Sum('amount', filter=Q(record_type='income')),
        total_expense=Sum('amount', filter=Q(record_type='expense')),
        record_count=Count('id'),
    )
    total_income = totals['total_income'] or 0
    total_expense = totals['total_expense'] or 0

    data = {
        'analysis_type': analysis_type or 'custom',
        'period': label,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': total_income - total_expense,
        'record_count': totals['record_count'],
        'category_breakdown': list(
            qs.values('category').annotate(
                total=Sum('amount'), count=Count('id'),
            ).order_by('-total')
        ),
        'top_expense_categories': list(
            qs.filter(record_type='expense')
            .values('category')
            .annotate(total=Sum('amount'))
            .order_by('-total')[:5]
        ),
    }

    if include_daily_trend:
        daily = list(
            qs.values('date')
            .annotate(
                income=Sum('amount', filter=Q(record_type='income')),
                expense=Sum('amount', filter=Q(record_type='expense')),
            )
            .order_by('date')
        )
        for entry in daily:
            entry['day'] = entry.pop('date').isoformat() if entry.get('date') else None
            entry['income'] = entry['income'] or 0
            entry['expense'] = entry['expense'] or 0
        data['daily_trend'] = daily

    if include_monthly_trend:
        monthly = list(
            qs.annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(
                income=Sum('amount', filter=Q(record_type='income')),
                expense=Sum('amount', filter=Q(record_type='expense')),
            )
            .order_by('month')
        )
        for entry in monthly:
            entry['month'] = entry['month'].strftime('%Y-%m') if entry['month'] else None
            entry['income'] = entry['income'] or 0
            entry['expense'] = entry['expense'] or 0
        data['monthly_trend'] = monthly

    context['data'] = data
    return render(request, 'analytics.html', context)

