require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; 
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";

$ret = &ReadParse(*in);

&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$inMIN      = $in{'min'};
$inMAX      = $in{'max'};

($inMIN) = &StripJunk($inMIN);
($inMAX) = &StripJunk($inMAX);

&readsetCookies;

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$mdate  = sprintf("%04d%02d%02d", $year, $month, $day);

if ( $USER ) {
  &MyReconRxHeader;
  &ReconRxHeaderBlock;
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

$dbin    = "RIDBNAME";  # Only database needed for this routine
if ($PH_ID == 11 || $PH_ID == 23) {
	$DBNAME  = "webinar";
} else {
	$DBNAME  = $DBNAMES{"$dbin"};
}
#print "DBNAME: $DBNAME\n";

my $FMT = "%0.02f";

#---------------------------------------
# Connect to the database

  $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
         { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
   
  DBI->trace(1) if ($dbitrace);
#---------------------------------------

&display_page;

$dbx->disconnect;

&MyReconRxTrailer;

exit(0);

sub display_page {

  $inmin = $inMIN;
  $inmax = $inMAX;

  $URLH = "${prog}.cgi";
  print qq#<FORM ACTION="$URLH" METHOD="POST">\n#;
  print qq#<INPUT TYPE="hidden" NAME="inmin"   VALUE="$inMIN">\n#;
  print qq#<INPUT TYPE="hidden" NAME="inmax"   VALUE="$inMAX">\n#;

  #jQuery now loaded on all pages via header include.
  print qq#<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.dataTables.css" /> \n#;
  print qq#<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.dataTables.min.css" /> \n#;
  print qq#<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.dataTables.dateTime.min.css" /> \n#;
  print qq#<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.buttons.dataTables.min.css" /> \n#;

##  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/jquery-3.5.1.js"></script> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/jquery.dataTablesV2.min.js"></script> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/dataTables.dateTime.min.js"></script> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/moment.min.js"></script> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/dataTables.buttons.min.js"></script> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/buttons.html5.min.js"></script> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/jszip.min.js"></script> \n#;

  print qq#<script type="text/javascript" charset="utf-8"> \n#;
  print qq# var minDate, maxDate; #;

  print qq#\$(document).ready(function() { \n#;
  print qq#  minDate = new DateTime(\$('\#min'), {
    });
    maxDate = new DateTime(\$('\#max'), {
    });
  #;

   print qq#   var table = \$('\#tablef').DataTable( {
                                  "bScrollCollapse": true,
                                  "sScrollY": "350px", 
                                  "bPaginate": false, 
      dom: 'Bfrtip',
        buttons: [
            'copyHtml5',
            'excelHtml5',
            'csvHtml5'
        ],
    	"footerCallback": function ( row, data, start, end, display ) {
            var api = this.api(), data;
 
            // converting to interger to find total
            var intVal = function ( i ) {
                return typeof i === 'string' ?
                    i.replace(/[\$,]/g, '')*1 :
                    typeof i === 'number' ?
                        i : 0;
            };
 
            var pageTotal = api
                .column( 2, { page: 'current'} )
                .data()
                .reduce( function (a, b) {
                    return intVal(a) + intVal(b);
                }, 0 );
            var claimTotal = api
                .column( 3, { page: 'current'} )
                .data()
                .reduce( function (a, b) {
                    return intVal(a) + intVal(b);
                }, 0 );
	   			
	   \$( api.column( 0 ).footer() ).html('Search Total');
           \$( api.column( 2 ).footer() ).html(formatter.format(pageTotal.toFixed(2)));
           \$( api.column( 3 ).footer() ).html(claimTotal);
       }
    } ); \n#;

  print qq# 
    \$('\#min, \#max').on('change', function () {
        table.draw();
    });
  #;
  print qq#} ); \n#;
  print qq# var formatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',

  });
  #;
  print qq#</script> \n#;

  print qq#<br>\n#;

  print qq#  <form action="$prog$ext" method="post">#;
    print qq#<table class='noborders'  cellspacing="5" cellpadding="5">
        <tbody><tr>
            <td>Minimum Date:</td>
            <td><input type="text" id="min" name="min" VALUE="$inmin"></td>
        </tr>
        <tr>
            <td>Maximum Date:</td>
            <td><input type="text" id="max" name="max" VALUE="$inmax"></td>
        </tr>
        <tr>
          <td><INPUT class="button-form" TYPE="submit" VALUE=">>>"></td>
        </tr>
      </tbody></table>
    </form>
  #;
  print qq#<br>\n#;
  print qq#<br>\n#;

  print qq#<table id="tablef">\n#;

  print qq#<thead>\n#;
  print qq#<tr>
             <th>TPP_Name</th>
             <th>BIN</th>
             <th>Total</th>
             <th>Count</th>\n#;
  print qq#</tr>\n#;
  print qq#</thead>\n#;

  print qq#<tbody>\n#;

  my $TotalPaid;
  my $TotalPaidPP;
  my $daterange = '';

  $SORTFIELD = "third_party_payer_name";

  my $sql = "";
  my $minrange;

  if ($inMIN ne '') {
    $minrange = $inMIN;
    $minrange =~ s/-//g;
  }
  if ($inMAX ne '') {
    $maxrange = $inMAX;
    $maxrange =~ s/-//g;
  }
  else {
    $maxrange = "$mdate";
  }
    $maxrange = "'$maxrange'";

  if($minrange) {
  $daterange = "&& dbdateofservice >= '$minrange' && dbdateofservice <= $maxrange";
  
  $sql = "
          SELECT third_party_payer_name, sum(dbTotalAmountPaid) as Total, dbBinParent, count(*), dbbinparentdbkey FROM (
            SELECT dbTotalAmountPaid, dbBinParent, dbbinparentdbkey 
              FROM $DBNAME.incomingtb 
             WHERE pharmacy_id IN ($PH_ID)
	            && dbResponseCode = 'P'
                && dbTotalAmountPaid > 0
                $daterange
          UNION ALL
            SELECT dbTotalAmountPaid, dbBinParent, dbbinparentdbkey 
            FROM $DBNAME.incomingtb_archive 
           WHERE pharmacy_id IN ($PH_ID)
                 $daterange
              && dbTotalAmountPaid > 0
              && dbTCode NOT REGEXP 'RVL' 
	      && dbTCode NOT REGEXP '^PDR\$'
	      && dbTCode NOT REGEXP '^RMR\$'
	      && dbTCode NOT REGEXP '^RNM\$'
        ) a
         JOIN officedb.third_party_payers b on a.dbBinParentdbkey = b.third_party_payer_id
	 group by dbBinParentdbkey 
         ORDER BY $SORTFIELD";
  ($sqlout = $sql) =~ s/\n/<br>\n/g;
  
  #print "sql: $sql\n";
  
  print "<hr>1. sql:<br>$sql<hr>\n" if ($debu24g);

  $TotalPaidPP = 0;
  $TotalPaid   = 0;

  $sthrp = $dbx->prepare($sql);
  $sthrp->execute();
  my $numofrows = $sthrp->rows;

  while ( my ($tpp_name, $TotalAmountPaid, $dbBinParent, $count, $tpp_pri ) = $sthrp->fetchrow_array()) {

    print qq#<tr>#;
    ##print qq#<td>$tpp_name</td>#;
    print qq#<td><a href="TotalSalesRpt_Dtl.cgi?TPP=$tpp_pri&min=$inMIN&max=$inMAX"> $tpp_name</a></td>#;
    print qq#<td>#, sprintf("%06d", $dbBinParent), qq#</td>#;
    print qq#<td>\$$TotalAmountPaid</td>#;
    print qq#<td>$count</td>#;
    print qq#</tr>\n#;

    $TotalPaid   += $TotalAmountPaid;
     
  }

  $sthrp->finish;
  }
 
  print qq#</tbody>\n#;
  print qq#<tfoot>\n
    <th></th>
    <th></th>
    <th></th>
    <th></th>
  #;
  print qq#</tfoot>\n#;

  $TotalPaid   = "\$" . &commify(sprintf("$FMT", $TotalPaid));
  print qq#<tr>#;
  print qq#</table>\n#;

  print qq#<div style="clear: both;"></div>#;
  print qq#<br>\n#;

  print qq#<div style="text-align: right; font-weight: bold; padding-right: 15px">\n#;

  print qq#Grand Sales Total: $TotalPaid<br>\n#;

  print qq#</div>\n#;

  print qq#</FORM>\n#;
}
