$(document).ready(function(){
    $('.sidenav').sidenav({edge: "right"});
  });

  $('.dropdown-trigger').dropdown();

  $(document).ready(function(){
    $('.collapsible').collapsible();

    $('.tooltipped').tooltip();

    $('.datepicker').datepicker({
        format: "dd mmmm, yyyy",
        yearRange: 3,
        showClearBtn: true,
        i18n: {
            done: "Select"
        }
    });

    $('select').formSelect();
  });
        