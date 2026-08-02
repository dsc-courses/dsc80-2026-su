---
layout: home
title: 🏠 Home
nav_exclude: false
nav_order: 1
# trigger rebuild
---

# {{ site.tagline }}

{: .mb-2 }
{{ site.description }}
{: .fs-6 .fw-300 }

{{ site.staffersnobio }}


{: .success }
Welcome to DSC 80! Make sure to read this website thoroughly and complete the items in the [Getting Started](https://dsc-courses.github.io/dsc80-2026-su/syllabus/#getting-started-) section of the syllabus. To join remote lecture, click the Zoom link from within Canvas.

[Jump to the current week](#{{ site.modules.first.title | slugify }}){: .btn data-current-week-link="" }
[Welcome Survey]({{ site.urls.welcome }}){: .btn }


{% for module in site.modules %}
{{ module }}
{% endfor %}


<script>
document.addEventListener('DOMContentLoaded', function() {
  var jumpLink = document.querySelector('[data-current-week-link]');
  if (!jumpLink) return;

  var modules = document.querySelectorAll('.module');
  if (!modules.length) return;

  var today = new Date();
  today.setHours(0, 0, 0, 0);

  var target = null;
  var i;

  for (i = modules.length - 1; i >= 0; i--) {
    var weekStart = modules[i].getAttribute('data-week-start');
    if (weekStart) {
      var startDate = new Date(weekStart + 'T00:00:00');
      if (today >= startDate) {
        target = modules[i].querySelector('.module-header');
        break;
      }
    }
  }

  if (!target && modules.length > 0) {
    target = modules[0].querySelector('.module-header');
  }

  if (target && target.id) {
    jumpLink.href = '#' + target.id;
    jumpLink.onclick = function(e) {
      e.preventDefault();
      location.hash = target.id;
      target.scrollIntoView({behavior: 'smooth', block: 'start'});
    };
  }
});
</script>
