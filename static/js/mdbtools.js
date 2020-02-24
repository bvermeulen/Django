/* Material Design for Bootstrap
   https://mdbootstrap.com/
   https://mdbootstrap.com/docs/jquery/tables/scroll/
*/
$(document).ready(function () {
  $('#dtHorizontalVerticalScroll').DataTable({
    "scrollX": true,
    "scrollY": "50vh",
    "scrollCollapse": true,
    "paging": false,
    "ordering": false,
    "searching": false,
    "info": false,
  });
  $('.dataTables_length').addClass('bs-select');
});
/* apply coding highlighting

*/
$('pre').each(function(i, block){
  hljs.highlightBlock(block);
});

/* set attribute 'data-aspectRatio' for all video frames and remove
   height and width attributes from the iframes
*/
var $allVideos = $("iframe[src^='https://player.vimeo.com'], iframe[src^='http://player.vimeo.com'], iframe[src^='https://www.youtube.com'], iframe[src^='http://www.youtube.com'], object, embed")
$allVideos.each(function() {
  $(this)
    // jQuery .data does not work on object/embed elements
    .attr('data-aspectRatio', this.height / this.width)
    .removeAttr('height')
    .removeAttr('width');
});

var hideElements = document.getElementsByClassName("hideOnMobile");

/* adjust displays on resizing of the window
*/
$(window).resize(function() {
  /* resize all video iframes relative to the parent container width; 100% for
     widths less than 600px and 60% for larger screens
  */
  $allVideos.each(function() {
    $parentWindow = $(this).parent();
    var newWidth = $parentWindow.width() * 1.00;
    if ($parentWindow.width() > 600) {
      var newWidth = $parentWindow.width() * 0.60;
    }
    var $el = $(this);
    $el
      .width(newWidth)
      .height(newWidth * $el.attr('data-aspectRatio'));
  });

  /* set width of chart-container id based on screen width
     parent width if width < 600px
     80% of parent width if width > 600px
  */
  $("#chart-container").each( function() {
    $parentWindow = $(this).parent();
    if ($parentWindow.width() < 600) {
      $(this).width($parentWindow.width());
    }
    else {
      $(this).width($parentWindow.width() * 0.8);
    }
  });

/* hide elements with class name hideOnMobile when screen is less than
   600 px
*/
  for (var i=0; i < hideElements.length; i++) {
    $(hideElements[i]).each( function() {
      $parentWindow = $(this).parent();
      if ($parentWindow.width() < 600) {
        $(this).hide();
      }
      else {
        $(this).show();
      }
    })
  }

}).resize();
