require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

use Excel::Writer::XLSX;  

$| = 1; # don't buffer output
#______________________________________________________________________________
#
my $cnt = 0;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
my $help = qq|\n\nExecute as "$prog " without debug, or add " -d" for debug|;

$nbsp = "&nbsp\;";
my $start_month;
my $start_year;
my $start;
my $end;
my $end_month;
my $end_year;
my $lastday;

$ret = &ReadParse(*in);

&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

#$PH_ID = 146;

#______________________________________________________________________________

&readsetCookies;

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);

($start_month, $start_year, $end_month, $end_year, $lastday) = &get_startend_month($month,$year,$sday);

$date_start = sprintf("%04d%02d%02d", $start_year, $start_month, 1);
$date_end   = sprintf("%04d%02d%02d", $end_year, $end_month, $lastday);
#______________________________________________________________________________

print qq#USER: $USER, VALID: $VALID, isMember: $isMember\n# if ($debug);

 ##<script type="text/javascript" src="../js/jqwidgets/scripts/jquery-1.11.1.min.js"></script>

if ( $USER ) {
  &MyReconRxHeader;
  &ReconRxHeaderBlock;
  print qq#
    <link rel="stylesheet" href="../js/jqwidgets/jqwidgets/styles/jqx.base.css" type="text/css" />
    <script type="text/javascript" src="../js/jqwidgets/jqwidgets/jqxcore.js"></script>
    <script type="text/javascript" src="../js/jqwidgets/jqwidgets/jqxbuttons.js"></script>
    <script type="text/javascript" src="../js/jqwidgets/jqwidgets/jqxscrollbar.js"></script>
    <script type="text/javascript" src="../js/jqwidgets/jqwidgets/jqxmenu.js"></script>
    <script type="text/javascript" src="../js/jqwidgets/jqwidgets/jqxdata.js"></script>
    <script type="text/javascript" src="../js/jqwidgets/jqwidgets/jqxgrid.js"></script>
    <script type="text/javascript" src="../js/jqwidgets/jqwidgets/jqxgrid.selection.js"></script>
    <script type="text/javascript" src="../js/jqwidgets/jqwidgets/jqxgrid.sort.js"></script>
    <script type="text/javascript" src="../js/jqwidgets/jqwidgets/jqxdata.export.js"></script> 
    <script type="text/javascript" src="../js/jqwidgets/jqwidgets/jqxgrid.export.js"></script>
 
    <script type="text/javascript" src="../js/jqwidgets/jqwidgets/jqxdropdownlist.js"></script>
    <script type="text/javascript" src="../js/jqwidgets/jqwidgets/jqxgrid.edit.js"></script>
    <script type="text/javascript" src="../js/jqwidgets/jqwidgets/jqxdropdownbutton.js"></script>
    <script type="text/javascript" src="../js/jqwidgets/jqwidgets/jqxgrid.columnsresize.js"></script>
    <script type="text/javascript" src="../js/jqwidgets/jqwidgets/jqxlistbox.js"></script>
    <script type="text/javascript" src="../js/jqwidgets/jqwidgets/jqxgrid.pager.js"></script>
   
  #;
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

$DBNAME = 'reconrxdb';

$dbx = DBI->connect("DBI:mysql:$DBNAME:$dbhost",$dbuser,$dbpwd,
        { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
             
DBI->trace(1) if ($dbitrace);


#______________________________________________________________________________

&readPharmacies();

$progext = "${prog}${ext}";

$ntitle = "Med Sync Patient Report for $Pharmacy_Names{$PH_ID}";
print qq#<h1 class="rbsreporting">$ntitle</h1>\n#;

print qq#<div id="jqxWidget">#;
print qq#<div id="jqxgrid"></div>#;
print qq#</div>#;
print qq#<input style='margin-top: 10px;' type="button" value="Export to Excel" id='excelExport' /> #;

#Additional Includes

print qq#
<form name="sbtc" action="$progext" method="post">

</form>

<hr />
#;

&getData($date_start, $date_end);

&logActivity($LOGIN, "Accessed MedSync Report in ReconRx", $PH_ID);

$dbx->disconnect;
 
#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub get_startend_month {
  $month = shift;
  $year  = shift;
  $day   = shift;

  my $start_month;
  my $start_year = $year;
  my $end_month;
  my $end_year   = $year;
  my $lastday;

  $start_month = $month -4;
  $end_month   = $month -1;
#  if ($day < 15) {
#    $start_month--;
#    $end_month--;
#  }

  if ($start_month < 1) {
    $start_month = 12 if ($start_month ==  0); 
    $start_month = 11 if ($start_month == -1); 
    $start_month = 10 if ($start_month == -2); 
    $start_month = 9  if ($start_month == -3); 
    $start_month = 8  if ($start_month == -4); 
    $start_year--;
  }

  if ($end_month < 1) {
    $end_month = 12 if ($end_month == 0); 
    $end_month = 11 if ($end_month < 0); 
    $end_year--;
  }

  my $wrk_month = $end_month;
  my $wrk_year = $end_year;
  for ( $x = 1; $x <= 4; $x++ ) {
    if ( $wrk_month < 1 ) {
      $wrk_month = 12;
      $wrk_year--;
    }

    $column = $wrk_year . sprintf("%02d", $wrk_month);

    push(@display_month, $column);
    $wrk_month--;
  }

  $lastday = &LastDayOfMonth($end_year,$end_month);
  return ($start_month, $start_year, $end_month, $end_year, $lastday);

}

sub getData {
  my $db = 'reconrxdb';
  my $tbl_medsync = 'rbs_medsync';
  my ($DateRangeStart, $DateRangeEnd) = @_;
#  $db = 'webinar' if($PH_ID < 12);

  print "sub getData: Entry.<br>\n" if ($debug);
  
  $starttime = time;
  $tth = time - $starttime;
  print "<p><hr />Time at entry of getData: $tth second(s)<hr /></p>\n" if ($showTTH);
  
  my $sql   = "";
  $start_month  = sprintf("%02d", $start_month);
  $end_month    = sprintf("%02d", $end_month);
  $lastday      = sprintf("%02d", $lastday);
  $start = "${start_year}${start_month}01";
  $end   = "$end_year$end_month$lastday";

  $sql  = "
    SELECT fname, lname, yob, synced, month1, month2, month3, month4, (month1+month2+month3+month4) AS Total
      FROM $db.$tbl_medsync
     WHERE Pharmacy_ID = $PH_ID
  ORDER BY Total DESC
  ";

  print "sql:<br>$sql<br>\n" if ($debug);

  $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  my $NumOfRows = $sthx->rows;
  print "Number of rows affected: $NumOfRows<br>\n" if ($debug);
  my $RepKeyLast = '';

  $grid = '[';

  while ( my @row = $sthx->fetchrow_array() ) {
    my ($fname, $lname, $yob, $synced, $month1, $month2, $month3, $month4, $total) = @row;
    if ( $NumOfRows > 0 ) {
      $fname =~ s/"//g;
      $lname =~ s/"//g;
      $fname =~ s/'/\\'/g;
      $lname =~ s/'/\\'/g;

#      $fname = substr($fname,0,1);
#      $fname .= '.';
#      $lname = substr($lname,0,3);
#      $lname .= '.';

      $grid .= "{
        'FName':'$fname',
        'LName':'$lname',
        'YOB':'$yob',
        'Synced':'$synced',
        'Cnt1':'$month1',
        'Cnt2':'$month2',
        'Cnt3':'$month3',
        'Cnt4':'$month4',
        'Total': '$total'
      },";
    }
  }

  $sthx->finish();

  $grid .= "]";

  print qq# <script>#;
  print qq^
\$(document).ready(function () {

// prepare the data

var month1 = $display_month[3];
var month2 = $display_month[2];
var month3 = $display_month[1];
var month4 = $display_month[0];

var source = {
    datatype: "json",
    datafields: [
        { name: 'FName', type:'string'},
        { name: 'LName', type:'string'},
        { name: 'YOB', type:'number'},
        { name: 'Synced', type:'string'},
        { name: 'Cnt1', type:'number'},
        { name: 'Cnt2', type:'number'},
        { name: 'Cnt3', type:'number'},
        { name: 'Cnt4', type:'number'},
        { name: 'Total', type:'number'}
    ],
    localdata: $grid,
    sortcolumn: 'Total',
    sortdirection: 'Desc',
};

var dataAdapter = new \$.jqx.dataAdapter(source);

         \$("#jqxgrid").jqxGrid(
            {
                width: 1000,
                height: 700,
                columnsheight: 40,
                source: dataAdapter,
                selectionmode: 'singlerow',
                editable:true,
    theme: 'classic',
    altrows: true,
    sortable: true,
    columns: [
        { text: 'First Name', datafield: 'FName', width: 100},
        { text: 'Last Name', datafield: 'LName', width: 100},
        { text: 'Year Of Birth', datafield: 'YOB', width: 100 },
        { text: 'Synced', datafield: 'Synced', width: 80 },
        { text: month1, datafield: 'Cnt1', width: 120},
        { text: month2, datafield: 'Cnt2', width: 120 },
        { text: month3, datafield: 'Cnt3', width: 120 },
        { text: month4, datafield: 'Cnt4', width: 120 },
        { text: 'Grand Total', datafield: 'Total', width: 120 }
    ]
            });

});

\$("#excelExport").jqxButton({
    theme: 'classic'
});

\$("#excelExport").click(function() {
    \$("#jqxgrid").jqxGrid('exportdata', 'xls', "$ntitle",true,null,null,'http://dev.pharmassess.com/js/jqwidgets/PHPExport/save-file.php'); 
});

  ^;
  print qq#</script>#;
}
