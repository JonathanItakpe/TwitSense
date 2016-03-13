/**
 * Created by PR0PH3T on 12/03/2016.
 */
$(function(){
    $("div").each(function(){
      var col_val = $(this).find("p").text();
        console.log(col_val)
      if ($.trim(col_val) == "Sentiment: positive"){
        $(this).addClass('success');  //the selected class colors the row green//
      } else {
        $(this).addClass('danger');
      }
    });
});
