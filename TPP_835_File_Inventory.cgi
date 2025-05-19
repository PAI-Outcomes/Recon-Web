require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use DateTime;
use Date::Calc qw(Add_Delta_Days Day_of_Week);
use Data::Dumper qw(Dumper);

my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

&readsetCookies;

my $bin      = $in{'bin'};

if ( $USER ) {
   &MyReconRxHeader;
   &ReconRxHeaderBlock;
} else {
   &ReconRxGotoNewLogin;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month++;

$month = sprintf("%02d", $month);
$day   = sprintf("%02d", $day);
$curr_date = "$year-$month-$day";

#______________________________________________________________________________

$dbin     = "R8DBNAME";
$DBNAME   = $DBNAMES{"$dbin"};
$TABLE    = $DBTABN{"$dbin"};
$FIELDS   = $DBFLDS{"$dbin"};
$FIELDS2  = $DBFLDS{"$dbin"} . "2";
$fieldcnt = $#${FIELDS2} + 2;

$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);

&displayWebPage;

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
  print qq#<!-- displayWebPage -->\n#;

  print "<style>
           td { border-top: none; }
         </style>";

  print qq#<form id="stopForm" action="$PROG" method="post" style="display: inline-block; padding-right: 30px;">#;
  print qq#<td><input type="hidden" name="sub_type" id="sub_type" value="Add">\n#;
  print "<table>\n";

  print qq#<tr><td><label for="BinNumber">Third Party Payer:</label></td>#;
  print qq#<td><input type="text" name="bin" list="blist" id="bin" value="" style="width:300px;">\n#;
  print qq#<datalist id="blist" >#;

  my $DBNAME = "officedb";
  my $TABLE  = "third_party_payers";

  my $sql = "SELECT Third_Party_Payer_ID, BIN, Third_Party_Payer_Name  
               FROM $DBNAME.$TABLE 
              WHERE Status = 'Active'
                 && Primary_Secondary = 'Pri'
                 && BIN != '000000' 
           ORDER BY Third_Party_Payer_Name";

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  while ( my ($TPP_ID, $TPP_BIN, $TPP_NAME) = $sthx->fetchrow_array() ) {
    print qq#<option value="$TPP_BIN - $TPP_NAME"> </option>\n#;
  }

  $sthx->finish;
  print qq# </datalist></td>#;

  print qq# <td><input type="submit" name="sub_type" value="Update"></td></tr>#;

  print qq#</table>\n#;

  print "</FORM>\n";

  print qq#<br /><hr />\n#;

  if ( $bin ) {
    $selected = substr($bin,9);
  }
  else {
    $selected = 'ALL';
  }


  print "<h2>TPP 835 File Inventory ($selected 835 Files Received)</h2>\n";

#  ($yaxis, $series) = &build_data();
  ($yaxis, $series, $ta_yaxis, $ta_series, $line_series) = &build_data();

#  print qq#YCATS: $yaxis<br>$series<br>#;

#    <div id="container" style="display: inline-block; height: 600px; width: 950px;"></div>
#    <div id="ta_container" style="display: inline-block; height: 375px; width: 250px;"></div>
#    <div id="line_graph" style="height: 400px; width: 1000px;"></div>
  print <<BM;
    <script src='https://code.highcharts.com/highcharts.js'></script>
    <script src='https://code.highcharts.com/modules/heatmap.js'></script>
    <script src='https://code.highcharts.com/modules/exporting.js'></script>
    <script src='https://code.highcharts.com/modules/export-data.js'></script>
    <script src='https://code.highcharts.com/modules/accessibility.js'></script>

    <script type="text/javascript" charset="utf-8">
      function getPointCategoryName(point, dimension) {
        var series = point.series,
          isY = dimension === 'y',
          axis = series[isY ? 'yAxis' : 'xAxis'];
        return axis.categories[point[isY ? 'y' : 'x']];
      }

      Highcharts.chart('container', {
        chart: {
          type: 'heatmap',
          marginTop: 40,
          marginBottom: 80,
          plotBorderWidth: 1
        },
        title: {
          text: ''
        },
        credits: {
          enabled: false
        },
        xAxis: [{
          categories: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
          },{
          linkedTo: 0,
          opposite: true,
          categories: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        }],
        yAxis: {
          categories: [$yaxis],
          title: null,
          reversed: true
        },
        colorAxis: {
          reversed: false,
          stops: [
            [0, '#ff0000'],
            [0.5, '#ffff00'],
            [1, '#008000']
          ],
          startOnTick: false,
          endOnTick: false,
        },
        legend: {
          align: 'right',
          layout: 'vertical',
          margin: 0,
          verticalAlign: 'top',
          y: 25,
          symbolHeight: 280
       },
       tooltip: {
         formatter: function () {
           return '<b>' + getPointCategoryName(this.point, 'x') + '</b> received <br><b>' +
           this.point.value + '</b> files';
         }
       },
       series: [{
         name: 'Files Received',
         borderWidth: 1,
         data: [$series],
          dataLabels: {
            enabled: true,
            color: '#000000'
          }
       }],
       responsive: {
         rules: [{
            condition: {
              maxWidth: 500
            }
         }]
       }
      });

      Highcharts.chart('ta_container', {
        chart: {
          type: 'heatmap',
          marginTop: 10,
          marginBottom: 80,
          plotBorderWidth: 1
        },
        title: {
          text: ''
        },
        credits: {
          enabled: false
        },
        xAxis: [{
          categories: ['Difference']
          },{
          linkedTo: 0,
          opposite: true,
          categories: ['Difference']
        }],
        yAxis: {
          categories: [$ta_yaxis],
          title: null,
          reversed: true
        },
        colorAxis: {
          reversed: false,
          stops: [
            [0, '#ff0000'],
            [0.5, '#ffff00'],
            [1, '#008000']
          ],
          startOnTick: false,
          endOnTick: false,
        },
        legend: {
          align: 'right',
          layout: 'vertical',
          margin: 0,
          verticalAlign: 'top',
          y: 25,
          symbolHeight: 200
       },
       tooltip: {
         formatter: function () {
           return 'Difference of <b>' +
           this.point.value + '</b> to weekly average';
         }
       },
       series: [{
         name: 'Files Received',
         borderWidth: 1,
         data: [$ta_series],
          dataLabels: {
            enabled: true,
            color: '#000000'
          }
       }],
       responsive: {
         rules: [{
            condition: {
              maxWidth: 500
            },
         }]
       }
     });

Highcharts.chart('line_graph', {
    title: {
        text: 'Total for Week'
    },
    credits: {
        enabled: false
    },
    xAxis: {
        categories: [ $yaxis ],
        crosshair: true
    },
    yAxis: {
        min: 0,
        title: {
            text: 'Number of Files'
        }
    },
    legend: {
        enabled: false
    },
    plotOptions: {
        column: {
            pointPadding: 0
        },
        series: {
            borderWidth: 0,
            dataLabels: {
                enabled: false,
                format: '{point.y:.2f}'
            }
        }
    },
    series: [{
        name: 'Weeks',
        data: [$line_series]
    }],
    responsive: {
        rules: [{
            condition: {
                maxWidth: 500
            },
            chartOptions: {
                legend: {
                    layout: 'horizontal',
                    align: 'center',
                    verticalAlign: 'bottom'
                }
            }
        }]
    }
});
</script>

<style>
.highcharts-figure, .highcharts-data-table table {
    min-width: 360px; 
    max-width: 900px;
    margin: 1em auto;
}

.highcharts-data-table table {
	font-family: Verdana, sans-serif;
	border-collapse: collapse;
	border: 1px solid #EBEBEB;
	margin: 10px auto;
	text-align: center;
	width: 100%;
	max-width: 500px;
}
.highcharts-data-table caption {
    padding: 1em 0;
    font-size: 1.2em;
    color: #555;
}
.highcharts-data-table th {
	font-weight: 600;
    padding: 0.5em;
}
.highcharts-data-table td, .highcharts-data-table th, .highcharts-data-table caption {
    padding: 0.5em;
}
.highcharts-data-table thead tr, .highcharts-data-table tr:nth-child(even) {
    background: #f8f8f8;
}
.highcharts-data-table tr:hover {
    background: #f1f7ff;
}
</style>
BM

}

#______________________________________________________________________________

sub build_data {
  my $sql = '';
  my $db = 'reconrxdb';
  my $tbl_p = '835remitstb';
  my $tbl_a = '835remitstb_archive';

  my $cats = '';
  my $series = '';
  my @weeks = ();
  my %day_rcvd = ();
  my %dow_counter = ();
  my %week_days = ();
  my $and = '';

  if ( $bin ) {
    $bin = substr($bin,0,6);
    $and = "AND R_ISA_BIN = '$bin'";
  }

  ($oyear,$omonth,$oday) = Add_Delta_Days($year,$month,$day, -180);
  $omonth = sprintf("%02d", $omonth);
  $oday   = sprintf("%02d", $oday);
  $end_date = "$oyear-$omonth-$oday";

  ($cats, @weeks) = get_weeks($end_date);

  $sql = "SELECT date_rcvd, count(*)
            FROM ( SELECT DISTINCT DATE(R_JAddedDate) AS date_rcvd, R_TPP, R_TPP_PRI, R_FTP_Filename
                     FROM $db.checks
                    WHERE R_JAddedDate >= '$end_date 00:00:00'
                     $and
                 ) x
        GROUP BY date_rcvd
        ORDER BY date_rcvd";

=cut
  $sql = "SELECT date_rcvd, count(*)
            FROM ( SELECT DISTINCT DATE(R_JAddedDate) AS date_rcvd, R_TPP, R_TPP_PRI, R_FTP_Filename
                     FROM $db.$tbl_p
                    WHERE R_JAddedDate >= '$end_date 00:00:00'
                     $and
                    UNION
                   SELECT DISTINCT DATE	(R_JAddedDate) AS date_rcvd, R_TPP, R_TPP_PRI, R_FTP_Filename
                     FROM $db.$tbl_a
                    WHERE R_JAddedDate >= '$end_date 00:00:00'
                     $and
                 ) x
        GROUP BY date_rcvd
        ORDER BY date_rcvd";
=cut

  my $sth = $dbx->prepare($sql);
  $rowsfound = $sth->execute;

##  print "SQL: $sql\n";

  while ( my ($date_rcvd, $file_count) = $sth->fetchrow_array() ) {
    $day_rcvd{$date_rcvd} = $file_count;
  }

  $sth->finish();

  my $y_counter = 0;

  foreach my $dte (@weeks) {
    my $file_counter = 0;
    my $date = $dte;
    for ( $x_counter = 6; $x_counter >= 0; --$x_counter ) {
      if ( $day_rcvd{$date} ) {
        $val = $day_rcvd{$date};
      }
      else {
        $val = 0;
      }

      $file_counter += $val;
      $series .= "[$x_counter, $y_counter, $val],";

      ($year, $month, $day) = split('-', $date);

      $dow = Day_of_Week($year,$month,$day);
      $dow_counter{$dow} += $val;
      push( @{$week_days{$dte}}, $val);

      ($year,$month,$day) = Add_Delta_Days($year,$month,$day, 1);
      $month = sprintf("%02d", $month);
      $day   = sprintf("%02d", $day);
      $date = "$year-$month-$day";
    }

    $y_counter++;

    $week_count{$dte} = $file_counter;
    $line_series .= "$file_counter,";
  }

  #### Get Rolling 12 Week Average
  my $week_counter = 0;
  @wrk_weeks = @weeks;

  foreach my $dte (@weeks) {
    ++$week_counter;
    next if ( $week_counter < 12 );

    my $cnt_weeks = 1;
    my $week_total = 0;

    for $x (0..11) {
      $week_total += $week_count{$wrk_weeks[$x]};
    }

    $weekly_avgs{$wrk_weeks[11]} = sprintf("%.2f", $week_count{$wrk_weeks[11]} - ($week_total/12));
    $weekly_avg_count{$wrk_weeks[11]} = sprintf("%.2f", ($week_total/12));

    shift(@wrk_weeks);
  }

  #### Generate Graph
#  print Dumper(\%week_days), "<br>";

  %dow_conv = ( '1' => '7', '2' => '1', '3' => '2', '4' => '3', '5' => '4', '6' => '5', '7' => '6' );

  print "<table>
           <thead>
             <tr>
               <th style='text-align: center;'>Week Beginning</th>
               <th style='text-align: center;'>Sunday</th>
               <th style='text-align: center;'>Monday</th>
               <th style='text-align: center;'>Tuesday</th>
               <th style='text-align: center;'>Wednesday</th>
               <th style='text-align: center;'>Thursday</th>
               <th style='text-align: center;'>Friday</th>
               <th style='text-align: center;'>Saturday</th>
               <th style='text-align: center;'>Week Avg</th>
               <th style='text-align: center;'>Rolling Avg</th>
               <th style='text-align: center;'>Diff</th>
             </tr>
           </thead><tbody>";

  foreach my $dte (@weeks) {
     print "<tr style='line-height: 12px;'><td style='text-align: center;'>$dte</td>";
     my $day_counter = 0;

     foreach $day ( @{$week_days{$dte}} ) {
       $day_counter++;

       $avg = $dow_counter{$dow_conv{$day_counter}}/25;
       $diff = $day - $avg;

       if ( $diff < 0 && $day/$avg < .80) {
         if ( $day/$avg >= .60 ) {
           $color = '#ffff1a'; # yellow
         }
         else {
           $color = '#ff1a1a'; # red
         }
       }
       else {
         $color = '#009900'; # green
       }

       print "<td style='background-color:$color; text-align: center; width: 100px; font-weight: bold; border: 1px solid #cccccc; border-collapse: collapse;'>$day</td>";
     }

     if ( $weekly_avgs{$dte} ) {
       $rolling_avg = $weekly_avg_count{$dte};
       $diff = $weekly_avgs{$dte};
       $border = '#cccccc';

       if ( $diff < 0 && $week_count{$dte}/$rolling_avg < .80) {
	     if ($avg == 0) {$avg = 1;} # Temp fix JDG 05/17/2023
	     if ( $day/$avg >= .60 ) {
           $color = '#ffff1a'; # yellow
         }
         else {
           $color = '#ff1a1a'; # red
         }
       }
       else {
         $color = '#009900'; # green
       }
     }
     else {
       $rolling_avg = '-';
       $diff = '-';
       $color = 'white';
       $border = 'none';
     }

     print "<td style='text-align: center; width: 90px; font-weight: bold;'>$week_count{$dte}</td>";
     print "<td style='text-align: center; width: 90px; font-weight: bold;'>$rolling_avg</td>";
     print "<td style='background-color:$color; text-align: center; width: 100px; font-weight: bold; border: 1px solid $border; border-collapse: collapse;'>$diff</td>";
     print "</tr>";
  }

  print "</tbody></table>";

  my $ta_series = '';
  my $ta_cats = '';
  $y_counter = 0;

  foreach my $date (sort keys %weekly_avgs) {
    $ta_series .= "[0, $y_counter, $weekly_avgs{$date}],";
    $ta_cats .= "'$date',";
    ++$y_counter;
  }

  chop($series);
  chop($line_series);
  chop($ta_series);
  chop($ta_cats);

  return($cats, $series, $ta_cats, $ta_series, $line_series);
}  

#______________________________________________________________________________

sub get_weeks {
  my $calc_date = shift @_;
  my $beg_found = 0;

  for (0..200) {
    last if ( $calc_date eq $curr_date );

    ($cyear, $cmonth, $cday) = split('-', $calc_date);
    ($cyear,$cmonth,$cday) = Add_Delta_Days($cyear,$cmonth,$cday, 1);
    $cmonth = sprintf("%02d", $cmonth);
    $cday   = sprintf("%02d", $cday);
    $calc_date = "$cyear-$cmonth-$cday";

    $dow = Day_of_Week($cyear,$cmonth,$cday);

    $beg_found = 1 if ( $dow == 7 );

    if ( $beg_found && $dow == 7 ) {
      $cats .= "'$calc_date',";
      push(@weeks, $calc_date);
    }
  }

  chop($cats);

  return($cats, @weeks);
}

