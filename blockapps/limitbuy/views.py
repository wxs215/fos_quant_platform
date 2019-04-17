from django.views.generic import ListView, DetailView, TemplateView,\
                            CreateView, UpdateView, DeleteView
from blockuser.models import QuantPolicyOrder
from .models import LimitbuyPolicy
from django.urls import reverse_lazy
from .tasks import run_limitbuy_policy
from django.views.generic.edit import ModelFormMixin
from django.core.urlresolvers import resolve
from django.core.exceptions import ValidationError

ITEMS_PER_PAGE = 5

class addLimitBuyView(CreateView):
    template_name = 'manage/limitbuy/limitbuy_create_form.html'
    model = LimitbuyPolicy
    fields = ['exchange', 'accesskey', 'secretkey', 'symbol', 'max_buy_price',\
               'min_sell_price', 'base_volume', 'limit_price', 'start_time', 'end_time']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url_name = resolve(self.request.path).url_name
        try:
            quantorder = QuantPolicyOrder.objects.get(user=self.request.user, policy_url_add=url_name)
            context['policy_start_time'] = quantorder.policy_start_time
            context['policy_end_time'] = quantorder.policy_end_time
        except:
            print('no quant order')
        return context
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        start_time = form.instance.start_time
        end_time = form.instance.end_time
        url_name = resolve(self.request.path).url_name
        try:
            quantorder = QuantPolicyOrder.objects.get(user=self.request.user, policy_url_add=url_name)
            if quantorder.policy_end_time < end_time:
                raise ValidationError("end time need to be less than %s" %(quantorder.policy_end_time))
            if quantorder.policy_start_time > start_time:
                raise ValidationError("start time need to be more than %s" %(quantorder.policy_start_time))
        except quantorder.DoesNotExist as e:
            print('quantorder does not exist')
        self.object = form.save()
        run_limitbuy_policy.delay(self.object.id)
        return super(ModelFormMixin, self).form_valid(form)

class updateLimitBuyView(UpdateView):
    template_name = 'manage/limitbuy/limitbuy_update_form.html'
    model = LimitbuyPolicy
    queryset = LimitbuyPolicy.objects.all()
    fields = ['exchange', 'accesskey', 'secretkey', 'symbol', 'max_buy_price',\
               'min_sell_price', 'base_volume', 'limit_price', 'start_time', 'end_time']

class deleteLimitBuyView(DeleteView):
    template_name = 'manage/limitbuy/limitbuy_delete_form.html'
    model = LimitbuyPolicy
    context_object_name = 'limitbuy_detail'
    success_url = reverse_lazy('manage_getlimitbuylist')

class getLimitBuyDetailView(DetailView):
    queryset = LimitbuyPolicy.objects.all()
    context_object_name = 'limitbuy_detail'
    template_name = 'manage/limitbuy/limitbuy_detail.html'

class getLimitBuyListView(ListView):
    queryset = LimitbuyPolicy.objects.order_by('-update_time')
    template_name = 'manage/limitbuy/limitbuy_list.html'
    context_object_name = 'limitbuy_list'
    paginate_by = ITEMS_PER_PAGE
    
    def get_context_data(self, **kwargs):
        return ListView.get_context_data(self, **kwargs)