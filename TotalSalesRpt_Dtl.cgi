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

$inTPP      = $in{'TPP'};
$inTPPNme   = $in{'inTPPNme'};
$SORT       = $in{'SORT'};
$inMIN      = $in{'min'};
$inMAX      = $in{'max'};

($inMIN) = &StripJunk($inMIN);
($inMAX) = &StripJunk($inMAX);


($inTPP) = &StripJunk($inTPP);

#______________________________________________________________________________

&readsetCookies;

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$maxdate = sprintf("%04d%02d%02d", $year, $month, $day);

##&readPharmacies;
&readThirdPartyPayers;

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
$DBNAME  = $DBNAMES{"$dbin"};

if ($PH_ID == 11 || $PH_ID == 23) {
    $DBNAME  = "webinar";
}

#print "DBNAME: $DBNAME\n";

$FMT = "%0.02f";

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
  print qq#<INPUT TYPE="hidden" NAME="db"      VALUE="$dbin">\n#;
  print qq#<INPUT TYPE="hidden" NAME="inTPP"   VALUE="$inTPP">\n#;
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
##  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/pdfmake.min.js"></script> \n#;
##  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/vfs_fonts.js"></script> \n#;

  print qq#<script type="text/javascript" charset="utf-8"> \n#;
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
            'csvHtml5',
            'pdfHtml5'
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
                .column( 6, { page: 'current'} )
                .data()
                .reduce( function (a, b) {
                    return intVal(a) + intVal(b);
                }, 0 );
	   			
           \$( api.column(5).footer() ).html(formatter.format(pageTotal.toFixed(2)));
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
             <th>PCN</th>
             <th>Rx</th>
             <th>Date Of Service</th>
             <th>Prescriber ID</th>
             <th>Amount Due</th>
             <th>Status</th>\n#;
  print qq#</tr>\n#;
  print qq#</thead>\n#;

  print qq#<tbody>\n#;

  my $TotalPaid;

  $SORTFIELD = "dbBinParentdbkey";

  if ($inMIN ne '') {
    $minrange = $inMIN;
    $minrange =~ s/-//g;
  }
  if ($inMAX ne '') {
    $maxrange = $inMAX;
    $maxrange =~ s/-//g;
  }
  else {
    $maxrange = "$maxdate";
  }
    $maxrange = "'$maxrange'";

  my $daterange = "&& dbdateofservice >= '$minrange' && dbdateofservice <= $maxrange"; ;
  

  my $sql = "";
  my $binsql = ""; 
  $binsql = "&& dbBinParentdbkey = '$inTPP'" if ($inTPP); 
  
  $sql = "SELECT * FROM (
          SELECT 'PROD' as DB, dbBinNumber,  dbBinParentdbkey, dbRxNumber, Date_Format(dbDateOfService,'%m/%d/%Y'), 
                 IFNULL(dbTotalAmountPaid_Remaining,0), IFNULL(dbTotalAmountPaid,0), dbProcessorControlNumber, dbTCode, dbPrescriberID
            FROM $DBNAME.incomingtb a
           WHERE pharmacy_id IN ($PH_ID)
            && dbTotalAmountPaid > 0
           $binsql
           $daterange
          UNION ALL
          SELECT 'ARCH' as DB, dbBinNumber, dbBinParentdbkey, dbRxNumber, Date_Format(dbDateOfService,'%m/%d/%Y'),
                 IFNULL(dbTotalAmountPaid_Remaining,0), IFNULL(dbTotalAmountPaid,0), dbProcessorControlNumber, dbTCode, dbPrescriberID
            FROM $DBNAME.incomingtb_archive a
           WHERE pharmacy_id IN ($PH_ID)
              $binsql
              $daterange
              && dbTotalAmountPaid > 0
              && dbTCode NOT REGEXP 'RVL' 
	      && dbTCode NOT REGEXP '^PDR\$'
	      && dbTCode NOT REGEXP '^RMR\$'
	      && dbTCode NOT REGEXP '^RNM\$'
        )a
        ORDER BY $SORTFIELD";
  ($sqlout = $sql) =~ s/\n/<br>\n/g;
  #print "sql: $sql\n";
  print "<hr>1. sql:<br>$sql<hr>\n" if ($debu24g);

  $TotalPaid   = 0;

  if($inMIN) {
  $sthrp = $dbx->prepare($sql);
  $sthrp->execute(); 
  my $numofrows = $sthrp->rows;

  while ( my ( $dbse, $dbBinNumber, $dbparent,  $dbRxNumber, $dbDateOfService, $dbTotalAmountPaid_Remaining, $dbTotalAmountPaid, $dbProcessorControlNumber, $dbCode, $dbPrescriberID ) = $sthrp->fetchrow_array()) {
    $tpp_name = $ThirdPartyPayer_Names{$dbparent};

    ##$checkmark = '';
    ## $checkmark = '<img src=\'checkmark.png\' style=\'width:20px;height:20px;\' />' if ($dbCode ne '');
    ##$checkmark = 'RECNO'  if ($dbCode eq '');

    $dbCode = 'ARCHIVE'  if ($dbCode eq 'BR');
    $dbCode = 'ARCHIVE'  if ($dbCode eq 'AABR');
    $dbCode = 'ARCHIVE'  if ($dbCode eq 'DUP');
    $dbCode = 'ARCHIVE'  if ($dbCode eq 'CUP');
    $dbCode = 'ARCHIVE'  if ($dbCode eq 'PDUP');

    if ($dbCode eq '' && $dbse eq 'ARCH') {
      $dbCode = 'RECONCILED';
    }
    
    print qq#<tr>#;

    print qq#<td>$tpp_name</td>#;
    print qq#<td>#, sprintf("%06d", $dbBinNumber), qq#</td>#;
    print qq#<td>$dbProcessorControlNumber</td>#;
    print qq#<td>$dbRxNumber</td>#;
    print qq#<td>$dbDateOfService</td>#;
    print qq#<td>$dbPrescriberID</td>#;
    print qq#<td>$dbTotalAmountPaid</td>#;
    print qq#<td>$dbCode</td>#;
    print qq#</tr>\n#;

    $TotalPaid   += $dbTotalAmountPaid;
     
  }

  $sthrp->finish;
  }
 
  print qq#</tbody>\n#;
  print qq#<tfoot>\n#;
  print qq#<tr>
    <th colspan="5" style="text-align:right">Search Total:</th>
    <th></th>#;
  print qq#</tr>\n#;
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
