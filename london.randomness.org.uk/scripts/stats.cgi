#!/opt/csw/bin/perl

use strict;
use warnings;

use lib "lib";

use CGI qw( :standard );
use CGI::Carp qw( fatalsToBrowser );
use OpenGuides;
use POSIX;
use RGL::Addons;
use OpenGuides::Config;
use OpenGuides::Utils;
use Template;

my $config_file = $ENV{OPENGUIDES_CONFIG_FILE} || "../wiki.conf";
my $config = OpenGuides::Config->new( file => $config_file );

my $guide = OpenGuides->new( config => $config );
my $wiki = $guide->wiki;

my %tt_vars = RGL::Addons->get_tt_vars( config => $config );

my $q = CGI->new;

my $dbh = $wiki->store->dbh;

my %sql = (
  edit_count     => "
    SELECT count(*)
    FROM content
                    ",
  username_count => "
    SELECT count(distinct metadata_value)
    FROM metadata
    WHERE metadata_type='username'
                    ",
  month_edit_count => "
    SELECT count(*)
    FROM content
    WHERE modified >= date_trunc( 'month', current_date ) - interval '1 month'
      AND modified < date_trunc( 'month', current_date)
                      ",
  month_username_count => "
    SELECT count( distinct metadata_value )
    FROM metadata
      INNER JOIN node ON node.id=metadata.node_id
                      AND node.version=metadata.version
    WHERE modified >= date_trunc( 'month', current_date ) - interval '1 month'
      AND modified < date_trunc( 'month', current_date)
      AND metadata_type='username'
                          ",
);

my %data;
foreach my $query ( keys %sql ) {
    my $sth = $dbh->prepare( $sql{$query} );
    $sth->execute or die $dbh->errstr;
    my ( $n ) = $sth->fetchrow_array;
    $data{$query} = $n;
}

$data{real_count}  = RGL::Addons->get_page_count( wiki => $wiki,
                                                  ignore_categories => 1,
                                                  ignore_locales => 1,
                                                );
$data{total_count} = RGL::Addons->get_page_count( wiki => $wiki );
$data{image_count} = RGL::Addons->get_num_photos( wiki => $wiki );

$data{month_real_count}  = RGL::Addons->get_page_count( wiki => $wiki,
                                                  ignore_categories => 1,
                                                  ignore_locales => 1,
                                                  added_last_month => 1,
                                                );
$data{month_total_count} = RGL::Addons->get_page_count( wiki => $wiki,
                                                  added_last_month => 1,
                                                );

$tt_vars{data} = \%data;

# Do the template stuff
my $custom_template_path = $config->custom_template_path || "";
my $template_path = $config->template_path;
my $tt = Template->new( { INCLUDE_PATH =>
                                   "$custom_template_path:$template_path"  } );

$tt_vars{addon_title} = "RGL Statistics";

print $q->header;
$tt->process( "stats.tt", \%tt_vars ) or die $tt->error;